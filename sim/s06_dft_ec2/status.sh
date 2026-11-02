#!/usr/bin/env bash
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; HERE="$LAB/sim/s06_dft_ec2"; source "$LAB/tools/aws/aws_env.sh"
IID=$(cat "$HERE/.instance_id"); IP=$(cat "$HERE/.instance_ip"); KEYF="$LAB/tools/aws/saltlab-dft.pem"
aws ec2 describe-instances --instance-ids "$IID" --query 'Reservations[0].Instances[0].[InstanceId,State.Name,LaunchTime]' --output text
ssh -i "$KEYF" -o ConnectTimeout=15 ubuntu@$IP 'cat /work/COST_STATUS.txt 2>/dev/null; cat /work/SETUP_DONE 2>/dev/null; cat /work/logs/vdw_check.txt 2>/dev/null; for s in READY RUNNING DONE FAILED; do echo "$s $(ls /work/jobs/*/$s 2>/dev/null | wc -l)"; done; uptime'
