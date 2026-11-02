#!/usr/bin/env bash
# Chain (3 Nov 2026): wait for the relax stage to finish, then write+run the fixed-geometry U-scan and the FM/AFM stage.
set -u
HERE="/Volumes/Aditya ssd/Salt-Battery-Lab/sim/s11_dft_chlorides"; cd "$HERE"; source ../../tools/env.sh >/dev/null 2>&1
while [ -f runs/.relax.lock ] && kill -0 "$(cat runs/.relax.lock)" 2>/dev/null; do sleep 30; done
for s in uscan mag; do
  python campaign.py write $s && python campaign.py run $s --lanes 3 --np 3
done
echo "chain finished $(date)"
