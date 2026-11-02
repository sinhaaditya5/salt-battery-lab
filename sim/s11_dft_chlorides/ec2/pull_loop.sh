#!/usr/bin/env bash
# Pull S11 results every 5 min (completion checked every minute) until /work/ALL_DONE (relax+uscan+mag+dos) exists (or the instance disappears), then one last pull.
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; HERE="$LAB/sim/s11_dft_chlorides/ec2"
IP=$(cat "$LAB/sim/s06_dft_ec2/.instance_ip"); KEYF="$LAB/tools/aws/saltlab-dft.pem"
fails=0
while true; do
  if "$HERE/ec2_s11.sh" pull >/dev/null 2>&1; then fails=0; else fails=$((fails+1)); fi
  ssh -i "$KEYF" -o ConnectTimeout=15 -o BatchMode=yes ubuntu@$IP 'test -f /work/ALL_DONE' 2>/dev/null && { "$HERE/ec2_s11.sh" pull; echo "queue done"; exit 0; }
  [ $fails -ge 3 ] && { echo "instance unreachable 3x; last pull $(cat "$LAB/sim/s11_dft_chlorides/runs/ec2_logs/LAST_PULL_UTC" 2>/dev/null)"; exit 2; }
  for i in 1 2 3 4 5; do ssh -i "$KEYF" -o ConnectTimeout=15 -o BatchMode=yes ubuntu@$IP "test -f /work/ALL_DONE" 2>/dev/null && break; sleep 60; done
done
