#!/usr/bin/env bash
# Launch the approved DFT spot instance (founder approval 2 Nov 2026: Ubuntu 24.04, c8g.8xlarge spot,
# ap-south-1, $25 cap, 48 h hard stop, root key for this job only). Prints instance id + IP.
set -euo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; HERE="$LAB/sim/s06_dft_ec2"; source "$LAB/tools/aws/aws_env.sh"
eval "$("$LAB/.venv/bin/python" -c "
import sys; sys.path.insert(0,'$LAB'); from params.product_params import EC2 as E
print(f\"REGION={E['region']} ITYPE={E['instance_type']} CAP={E['spend_cap_usd']} HARD={int(E['hard_shutdown_hours'])} EBS={E['ebs_gb']}\")")"
# per-job overrides (3 Nov 2026 S11 chloride run: shorter hard stop, lower per-instance cap)
ITYPE=${S06_ITYPE:-$ITYPE}; CAP=${S06_CAP_USD:-$CAP}; HARD=${S06_HARD_HOURS:-$HARD}; EBS=${S06_EBS_GB:-$EBS}
ARCH=${S06_ARCH:-arm64}            # arm64 (Graviton, DFT) or amd64 (x86: Blender/KiCad/LibreOffice build host)
MAXPRICE=${S06_MAXPRICE:-0.45}     # spot max $/h; worst case 48 h x 0.45 + EBS/IPv4 < $25 cap (per-job override S06_MAXPRICE)
KEY=saltlab-dft; KEYF="$LAB/tools/aws/$KEY.pem"; SG=saltlab-dft-ssh
AMI=$(aws ssm get-parameter --region $REGION --name /aws/service/canonical/ubuntu/server/24.04/stable/current/$ARCH/hvm/ebs-gp3/ami-id --query Parameter.Value --output text)
if [ ! -f "$KEYF" ]; then
  aws ec2 create-key-pair --region $REGION --key-name $KEY --key-type ed25519 --query KeyMaterial --output text > "$KEYF"; chmod 600 "$KEYF"
fi
MYIP=$(curl -s https://checkip.amazonaws.com | tr -d '\n')
VPC=$(aws ec2 describe-vpcs --region $REGION --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SGID=$(aws ec2 describe-security-groups --region $REGION --filters Name=group-name,Values=$SG Name=vpc-id,Values=$VPC --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || true)
if [ "$SGID" = "None" ] || [ -z "$SGID" ]; then
  SGID=$(aws ec2 create-security-group --region $REGION --group-name $SG --description "Salt Battery DFT SSH from founder IP only" --vpc-id $VPC --query GroupId --output text)
fi
aws ec2 authorize-security-group-ingress --region $REGION --group-id $SGID --protocol tcp --port 22 --cidr "$MYIP/32" 2>/dev/null || true
sed -e "s/__HARD_HOURS__/$HARD/" -e "s/__CAP_USD__/$CAP/" -e "s/__PRICE_USD_H__/$MAXPRICE/" "$HERE/cloud_init.sh" > "$HERE/.user_data.rendered.sh"
IID=$(aws ec2 run-instances --region $REGION --image-id $AMI --instance-type $ITYPE --key-name $KEY \
  --security-group-ids $SGID \
  --instance-market-options "MarketType=spot,SpotOptions={MaxPrice=$MAXPRICE,SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}" \
  --instance-initiated-shutdown-behavior terminate \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$EBS,VolumeType=gp3,DeleteOnTermination=true}" \
  --user-data "file://$HERE/.user_data.rendered.sh" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=saltlab-dft},{Key=project,Value=salt-battery-lab}]" \
  --query 'Instances[0].InstanceId' --output text)
echo "$IID" > "$HERE/.instance_id"; date -u +%FT%TZ > "$HERE/.launched_utc"
aws ec2 wait instance-running --region $REGION --instance-ids $IID
IP=$(aws ec2 describe-instances --region $REGION --instance-ids $IID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "$IP" > "$HERE/.instance_ip"
echo "launched $IID ($ITYPE spot, max \$$MAXPRICE/h) at $IP; hard stop ${HARD} h; cap \$$CAP"
