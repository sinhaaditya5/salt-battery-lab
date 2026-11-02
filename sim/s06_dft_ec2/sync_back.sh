#!/usr/bin/env bash
# Pull results back to the SSD (outputs + logs; wavefunctions are never kept on the instance).
# Usage: ./sync_back.sh            one pull
#        ./sync_back.sh --loop     pull every 20 min until the instance is gone
set -uo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; HERE="$LAB/sim/s06_dft_ec2"
IP=$(cat "$HERE/.instance_ip"); KEYF="$LAB/tools/aws/saltlab-dft.pem"
SSH="ssh -i '$KEYF' -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20"
pull() { rsync -az --exclude 'tmp/' --exclude '*.wfc*' -e "$SSH" ubuntu@$IP:/work/ "$HERE/runs/" && date -u +%FT%TZ > "$HERE/runs/LAST_PULL_UTC"; }
mkdir -p "$HERE/runs"
if [ "${1:-}" = "--loop" ]; then
  while pull; do sleep 1200; done; echo "instance unreachable; last pull $(cat "$HERE/runs/LAST_PULL_UTC" 2>/dev/null)"
else pull; fi
