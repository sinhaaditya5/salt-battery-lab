#!/bin/bash
# Queue runner on the EC2 instance. Lanes run in parallel, each with RANKS MPI ranks.
# A job = /work/jobs/<lane>_<name>/ with pw.in + READY. States: READY -> RUNNING -> DONE | FAILED.
# Usage (as ubuntu): nohup /work/run_queue.sh > /work/logs/queue.log 2>&1 &
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PATH=/work/mamba/envs/qe/bin:$PATH   # conda-forge QE 7.6 (apt QE 6.7 on noble aborts: fortify buffer overflow)
RANKS=${RANKS:-8}
cd /work
# 0) dispersion keyword check: QE 6.7 must accept grimme-d3, else fall back to grimme-d2 (logged)
mkdir -p /work/selftest && cd /work/selftest
awk '/&SYSTEM/{print; print "  vdw_corr = '\''grimme-d3'\''"; next}1' /work/jobs/A_Na_bcc/pw.in | sed "s/prefix = 'Na_bcc'/prefix = 'd3test'/" > d3.in
if mpirun --bind-to none -np 2 pw.x -in d3.in > d3.out 2>&1 && grep -q "JOB DONE" d3.out; then echo "grimme-d3 OK" > /work/logs/vdw_check.txt
else echo "grimme-d3 FAILED -> using grimme-d2" > /work/logs/vdw_check.txt; sed -i "s/vdw_corr = 'grimme-d3'/vdw_corr = 'grimme-d2'/" /work/jobs/*/pw.in; fi
cd /work
lane() {
  L=$1; CPUS=$2
  while true; do
    j=$(ls -d /work/jobs/${L}_*/ 2>/dev/null | while read d; do [ -f "$d/READY" ] && echo "$d"; done | head -1)
    if [ -z "$j" ]; then
      # nothing left in this lane: steal READY work from any lane
      j=$(ls -d /work/jobs/*/ 2>/dev/null | while read d; do [ -f "$d/READY" ] && echo "$d"; done | head -1)
    fi
    [ -z "$j" ] && break
    mv "$j/READY" "$j/RUNNING" 2>/dev/null || continue
    cd "$j"; echo "$(date -u +%FT%TZ) start $(basename $j) lane $L" >> /work/logs/queue.log
    t0=$(date +%s)
    if taskset -c $CPUS mpirun --bind-to none -np $RANKS pw.x -nk 2 -in pw.in > pw.out 2> pw.err && grep -q "JOB DONE" pw.out; then
      echo $(( $(date +%s) - t0 )) > WALL_SECONDS; mv RUNNING DONE
    else
      echo $(( $(date +%s) - t0 )) > WALL_SECONDS; mv RUNNING FAILED
    fi
    rm -rf tmp/*.save/wfc* tmp/*.wfc* 2>/dev/null
    echo "$(date -u +%FT%TZ) end $(basename $j) $(ls DONE FAILED 2>/dev/null)" >> /work/logs/queue.log
    cd /work
  done
}
NL=${NLANES:-4}
lane A 0-7 & lane B 8-15 & lane C 16-23 & lane D 24-31 &
wait
touch /work/QUEUE_DONE
echo "$(date -u +%FT%TZ) queue finished" >> /work/logs/queue.log
