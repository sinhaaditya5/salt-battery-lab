#!/usr/bin/env bash
# Push pseudopotentials, queue runner and job folders to the instance (only jobs not already there).
set -euo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; HERE="$LAB/sim/s06_dft_ec2"
IP=$(cat "$HERE/.instance_ip"); KEYF="$LAB/tools/aws/saltlab-dft.pem"
SSH="ssh -i '$KEYF' -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20"
rsync -az -e "$SSH" "$LAB/tools/pseudo/gbrv/"{li_pbe_v1.4,na_pbe_v1.5,mn_pbe_v1.5,fe_pbe_v1.5,ti_pbe_v1.4,p_pbe_v1.5,o_pbe_v1.2,h_pbe_v1.4,c_pbe_v1.2,n_pbe_v1.2}.uspp.F.UPF ubuntu@$IP:/work/pseudo/
rsync -az -e "$SSH" "$HERE/run_queue.sh" ubuntu@$IP:/work/
# only push job folders that do not exist remotely (re-sending would resurrect READY markers of started jobs)
REMOTE=$(ssh -i "$KEYF" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 ubuntu@$IP 'ls /work/jobs 2>/dev/null')
for d in "$HERE"/jobs/*/; do n=$(basename "$d"); if ! grep -qx "$n" <<< "$REMOTE"; then rsync -az -e "$SSH" "$d" "ubuntu@$IP:/work/jobs/$n/"; echo "pushed $n"; fi; done
echo "synced to $IP"
