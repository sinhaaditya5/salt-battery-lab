#!/bin/bash
# Runs ON the instance after remote_run.sh (waits for /work/QUEUE_DONE): PDOS stage = SCF (k 30 A, 40 bands) + projwfc.x.
set -u
L=/work/lab; S=$L/sim/s11_dft_chlorides; QE=$L/tools/micromamba/envs/qe/bin
exec >> /work/logs/s11_dos.log 2>&1
while [ ! -f /work/QUEUE_DONE ]; do sleep 20; done
cd $S; export OMP_NUM_THREADS=1
$QE/python campaign.py write dos && $QE/python campaign.py run dos --lanes 2 --np 16 --nk 4
for d in runs/dos/*_keep; do
  ( cd "$d" && "$QE/mpirun" --oversubscribe -np 4 "$QE/projwfc.x" -in projwfc.in > projwfc.out 2>&1
    if grep -q "JOB DONE" projwfc.out; then echo "$(date -u +%FT%TZ) projwfc $d DONE"; else echo "$(date -u +%FT%TZ) projwfc $d FAILED"; fi
    rm -rf tmp )
done
echo "$(date -u +%FT%TZ) dos finished"; touch /work/ALL_DONE
