#!/bin/bash
# Runs ON the EC2 instance (as ubuntu). Mirrors the lab layout under /work/lab so campaign.py runs unchanged:
#   /work/lab/tools/micromamba/envs/qe/bin  (conda-forge QE 7.6 + OpenMPI + numpy)
#   /work/lab/tools/pseudo/gbrv             (the 5 GBRV files, checksums in PROJECT_SALT/.../PROVENANCE.md)
#   /work/lab/sim/s11_dft_chlorides         (campaign.py + runs/relax)
# Stages: relax (NiCl2 U0/U4 only; others already DONE locally) -> uscan (24 SCF) -> mag (12 SCF).
set -u
L=/work/lab; S=$L/sim/s11_dft_chlorides; LOG=/work/logs/s11.log; mkdir -p /work/logs
exec >> "$LOG" 2>&1
echo "$(date -u +%FT%TZ) s11 remote start"
while [ ! -f /work/SETUP_DONE ]; do sleep 10; done          # cloud-init apt step must finish (apt lock)
if [ ! -x $L/tools/micromamba/envs/qe/bin/pw.x ]; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q bzip2 >/dev/null
  cd /work && curl -Ls https://micro.mamba.pm/api/micromamba/linux-aarch64/latest | tar -xj bin/micromamba
  MAMBA_ROOT_PREFIX=$L/tools/micromamba /work/bin/micromamba create -y -q -n qe -c conda-forge "qe=7.6" openmpi python=3.12 numpy > /work/logs/mamba.log 2>&1
fi
PY=$L/tools/micromamba/envs/qe/bin/python
$L/tools/micromamba/envs/qe/bin/pw.x -h > /dev/null 2>&1; ls $L/tools/micromamba/conda-meta 2>/dev/null; ls $L/tools/micromamba/envs/qe/conda-meta | grep -E "^qe-[0-9]" > /work/logs/qe_version.txt
cd $S
sed -i "s#pseudo_dir='[^']*'#pseudo_dir='$L/tools/pseudo/gbrv'#" runs/relax/*/job.in
export OMP_NUM_THREADS=1
$PY campaign.py run relax --lanes 2 --np 16 --nk 4
for st in uscan mag; do $PY campaign.py write $st && $PY campaign.py run $st --lanes 4 --np 8 --nk 4; done
echo "$(date -u +%FT%TZ) s11 remote finished"; touch /work/QUEUE_DONE
