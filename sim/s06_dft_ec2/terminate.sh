#!/usr/bin/env bash
# Pull results one last time, then terminate the instance and delete its key pair + security group.
set -uo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; HERE="$LAB/sim/s06_dft_ec2"; source "$LAB/tools/aws/aws_env.sh"
"$HERE/sync_back.sh" || true
IID=$(cat "$HERE/.instance_id")
aws ec2 terminate-instances --instance-ids "$IID" --query 'TerminatingInstances[0].CurrentState.Name' --output text
aws ec2 wait instance-terminated --instance-ids "$IID"
SGID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=saltlab-dft-ssh --query 'SecurityGroups[0].GroupId' --output text)
aws ec2 delete-security-group --group-id "$SGID" || true
aws ec2 delete-key-pair --key-name saltlab-dft || true
echo "terminated $IID; security group and key pair removed"
