#!/usr/bin/env bash
# Drive the S11 chloride campaign on the S6 EC2 instance (launch with ../../s06_dft_ec2/launch.sh first).
# Usage: ./ec2_s11.sh push      upload campaign + relax geometries + pseudos, start remote_run.sh and remote_dos.sh
#        ./ec2_s11.sh status    progress
#        ./ec2_s11.sh pull      copy relax/uscan/mag results + logs back into ../runs (never deletes local files)
set -euo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; S11="$LAB/sim/s11_dft_chlorides"; S06="$LAB/sim/s06_dft_ec2"
IP=$(cat "$S06/.instance_ip"); KEYF="$LAB/tools/aws/saltlab-dft.pem"
SSHO=(-i "$KEYF" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20); SSH="ssh -i '$KEYF' -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20"
R=ubuntu@$IP; RL=/work/lab
case "${1:-}" in
push)
  ssh "${SSHO[@]}" $R "mkdir -p $RL/tools/pseudo/gbrv $RL/sim/s11_dft_chlorides/runs"
  rsync -az -e "$SSH" "$LAB/tools/pseudo/gbrv/"{na_pbe_v1.5,cl_pbe_v1.4,fe_pbe_v1.5,co_pbe_v1.2,ni_pbe_v1.4}.uspp.F.UPF $R:$RL/tools/pseudo/gbrv/
  rsync -az -e "$SSH" "$S11/campaign.py" "$S11/ec2/remote_run.sh" "$S11/ec2/remote_dos.sh" $R:$RL/sim/s11_dft_chlorides/
  rsync -az --exclude tmp/ -e "$SSH" "$S11/runs/relax" $R:$RL/sim/s11_dft_chlorides/runs/
  ssh "${SSHO[@]}" $R "cd $RL/sim/s11_dft_chlorides; chmod +x remote_run.sh remote_dos.sh; (nohup ./remote_run.sh > /dev/null 2>&1 &); (nohup ./remote_dos.sh > /dev/null 2>&1 &); sleep 2; pgrep -f remote_run.sh >/dev/null && echo started";;
dos)   # add the PDOS stage to an instance that is already running remote_run.sh (3 Nov 2026)
  rsync -az -e "$SSH" "$S11/campaign.py" "$S11/ec2/remote_dos.sh" $R:$RL/sim/s11_dft_chlorides/
  ssh "${SSHO[@]}" $R "cd $RL/sim/s11_dft_chlorides; chmod +x remote_dos.sh; (nohup ./remote_dos.sh > /dev/null 2>&1 &); sleep 2; pgrep -f remote_dos.sh >/dev/null && echo dos-queued";;
status)
  ssh "${SSHO[@]}" $R "cat /work/COST_STATUS.txt; tail -4 /work/logs/s11.log; tail -6 $RL/sim/s11_dft_chlorides/runs/campaign.log 2>/dev/null; uptime";;
pull)
  # relax: only the jobs run on EC2 (the rest ran locally; their job.in must keep the local pseudo_dir)
  for j in NiCl2_FM_U0 NiCl2_FM_U4; do
    rsync -az --exclude tmp/ -e "$SSH" $R:$RL/sim/s11_dft_chlorides/runs/relax/$j "$S11/runs/relax/" 2>/dev/null || true
  done
  for st in uscan mag dos; do
    rsync -az --exclude tmp/ -e "$SSH" $R:$RL/sim/s11_dft_chlorides/runs/$st "$S11/runs/" 2>/dev/null || true
  done
  mkdir -p "$S11/runs/ec2_logs"
  rsync -az -e "$SSH" $R:$RL/sim/s11_dft_chlorides/runs/campaign.log "$S11/runs/ec2_logs/campaign_ec2.log" 2>/dev/null || true
  rsync -az -e "$SSH" $R:/work/logs/ $R:/work/COST_STATUS.txt "$S11/runs/ec2_logs/" 2>/dev/null || true
  date -u +%FT%TZ > "$S11/runs/ec2_logs/LAST_PULL_UTC"; echo "pulled $(cat "$S11/runs/ec2_logs/LAST_PULL_UTC")";;
*) sed -n 2,6p "$0"; exit 1;;
esac
