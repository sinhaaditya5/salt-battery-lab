#!/bin/bash
# EC2 user-data for the Salt Battery DFT+U job (Ubuntu 24.04 arm64, c8g.8xlarge spot).
# - installs Quantum ESPRESSO 6.7 (Ubuntu apt) + OpenBLAS + OpenMPI
# - arms a HARD auto-shutdown (instance-initiated shutdown => terminate) after HARD_HOURS
# - starts a cost watchdog that also shuts down when the estimated spend reaches the cap
set -euxo pipefail
HARD_HOURS=__HARD_HOURS__
CAP_USD=__CAP_USD__
PRICE_USD_H=__PRICE_USD_H__
# 1) Hard timer first, before anything else can fail.
shutdown -h +$((HARD_HOURS*60)) "Salt-Battery DFT hard stop after ${HARD_HOURS} h" || true
date -u +%s > /var/tmp/boot_epoch
# 2) Cost watchdog (max spot price x elapsed hours, + EBS/IPv4 allowance).
cat > /usr/local/bin/cost_watchdog.sh <<WD
#!/bin/bash
while true; do
  now=\$(date -u +%s); b=\$(cat /var/tmp/boot_epoch); h=\$(echo "(\$now-\$b)/3600" | bc -l)
  usd=\$(echo "\$h*$PRICE_USD_H + \$h*0.01" | bc -l)
  echo "\$(date -u +%FT%TZ) hours=\$h est_usd=\$usd cap=$CAP_USD" > /work/COST_STATUS.txt
  if (( \$(echo "\$usd >= $CAP_USD" | bc -l) )); then echo "cap reached" >> /work/COST_STATUS.txt; sync; shutdown -h now; fi
  # stop early when the queue is finished and idle for 2 h (results must be pulled before that)
  if [ -f /work/QUEUE_DONE ] && [ \$(( now - \$(stat -c %Y /work/QUEUE_DONE) )) -gt 7200 ]; then echo "idle stop" >> /work/COST_STATUS.txt; sync; shutdown -h now; fi
  sleep 300
done
WD
chmod +x /usr/local/bin/cost_watchdog.sh
mkdir -p /work/jobs /work/pseudo /work/logs
chown -R ubuntu:ubuntu /work
nohup /usr/local/bin/cost_watchdog.sh >/dev/null 2>&1 &
# 3) Software.
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends quantum-espresso libopenblas0-pthread openmpi-bin bc rsync htop
update-alternatives --set libblas.so.3-aarch64-linux-gnu /usr/lib/aarch64-linux-gnu/openblas-pthread/libblas.so.3 || true
update-alternatives --set liblapack.so.3-aarch64-linux-gnu /usr/lib/aarch64-linux-gnu/openblas-pthread/liblapack.so.3 || true
pw.x -h >/dev/null 2>&1 || true
echo "QE ready: $(dpkg -s quantum-espresso | grep Version)" > /work/SETUP_DONE
chown -R ubuntu:ubuntu /work
