#!/usr/bin/env bash
# Drive the x86 EC2 build host (Blender / KiCad / CADCraft / LibreOffice / Python generators run THERE, not on the laptop).
# Launch first:  S06_ARCH=amd64 S06_ITYPE=c7i.8xlarge S06_MAXPRICE=0.75 S06_HARD_HOURS=10 S06_CAP_USD=10 S06_EBS_GB=80 sim/s06_dft_ec2/launch.sh
# Usage:
#   ec2_build.sh push                 sync the lab (no secrets, no caches) + CADCraft source to /work
#   ec2_build.sh bootstrap            start tools/ec2_build/bootstrap.sh (toolchain install, ~15-20 min)
#   ec2_build.sh run  "<cmd>"         run a command in the lab with tools/env.sh sourced (foreground)
#   ec2_build.sh bg   <name> "<cmd>"  same, in the background; log /work/logs/<name>.log, marker /work/done/<name>.{ok,fail}
#   ec2_build.sh status               bootstrap/background-job state, load, cost watchdog
#   ec2_build.sh pull                 copy generated files back (never deletes local files; skips files newer locally)
# Finish with sim/s06_dft_ec2/terminate.sh (or aws ec2 terminate-instances).
set -uo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; S06="$LAB/sim/s06_dft_ec2"; PARC="/Volumes/Aditya ssd/PARC-Delta-Lab"
IP=$(cat "$S06/.instance_ip"); KEYF="$LAB/tools/aws/saltlab-dft.pem"; R=ubuntu@$IP
SSHO=(-i "$KEYF" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o ServerAliveInterval=30)
SSH="ssh -i '$KEYF' -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o ServerAliveInterval=30"
EXCL=(--exclude .git/ --exclude .venv/ --exclude tools/micromamba/ --exclude tools/cache/ --exclude tools/uv-cache/ --exclude tools/tmp/
      --exclude tools/blender-user/ --exclude tools/lo_profile/ --exclude tools/aws/ --exclude rootkey.csv --exclude '*.pem' --exclude '*.lck'
      --exclude renders/out/turntable/ --exclude renders/out/turntable_captioned/ --exclude sim/s06_dft_ec2/runs/ --exclude sim/s06_dft_ec2/runs_i1/
      --exclude DELIVERABLES.zip --exclude work/ --exclude __pycache__/ --exclude .DS_Store --exclude '.instance_*' --exclude .user_data.rendered.sh)
rsh() { ssh "${SSHO[@]}" $R "$@"; }
case "${1:-}" in
push)
  rsh "mkdir -p /work/lab /work/cadcraft /work/logs /work/done"
  # --update: never overwrite a file that is newer on the build host (outputs generated there after the last pull)
  rsync -azu "${EXCL[@]}" -e "$SSH" "$LAB/" $R:/work/lab/ && echo "lab synced"
  rsync -az --exclude target/ --exclude .git/ -e "$SSH" "$PARC/tools/cadcraft/" $R:/work/cadcraft/ && echo "cadcraft source synced";;
bootstrap)
  rsh "chmod +x /work/lab/tools/ec2_build/bootstrap.sh; (nohup /work/lab/tools/ec2_build/bootstrap.sh > /dev/null 2>&1 &); sleep 2; pgrep -f bootstrap.sh > /dev/null && echo bootstrap-started";;
run)
  rsh "cd '/Volumes/Aditya ssd/Salt-Battery-Lab' && source tools/env.sh >/dev/null 2>&1 && $2";;
bg)
  n="$2"; c="$3"
  rsh "mkdir -p /work/done; rm -f /work/done/$n.ok /work/done/$n.fail; cd '/Volumes/Aditya ssd/Salt-Battery-Lab' || exit 1; (nohup bash -c 'source tools/env.sh >/dev/null 2>&1; $c' > /work/logs/$n.log 2>&1 < /dev/null && touch /work/done/$n.ok || touch /work/done/$n.fail) > /dev/null 2>&1 < /dev/null & disown; echo started $n";;
status)
  rsh 'cat /work/COST_STATUS.txt 2>/dev/null; ls /work/BOOTSTRAP_DONE 2>/dev/null; tail -2 /work/logs/bootstrap.log 2>/dev/null; ls /work/done 2>/dev/null | tr "\n" " "; echo; uptime';;
pull)
  rsync -azu "${EXCL[@]}" -e "$SSH" $R:/work/lab/ "$LAB/" && echo "pulled $(date -u +%FT%TZ)"
  mkdir -p "$LAB/tools/ec2_build/logs"; rsync -az -e "$SSH" $R:/work/logs/ "$LAB/tools/ec2_build/logs/";;
*) sed -n 2,13p "$0"; exit 1;;
esac
