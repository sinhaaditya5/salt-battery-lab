#!/bin/bash
# Build-host bootstrap (runs ON an x86_64 Ubuntu 24.04 EC2 instance as ubuntu; launched by tools/ec2_build/ec2_build.sh).
# Mirrors the lab toolchain of the founder's Mac so every generator runs unchanged:
#   Blender 5.0.1 (official linux-x64), KiCad 10 (kicad PPA, + symbols/footprints/3D), LibreOffice (headless),
#   Python 3.12 venv from tools/ec2_build/requirements.txt (uv), Rust + CADCraft CLI (built from the PARC source),
#   Freerouting (Java autorouter), Xvfb (screenshots), ffmpeg (turntable video).
# The lab is synced to /work/lab and exposed at its Mac path "/Volumes/Aditya ssd/Salt-Battery-Lab" (symlink),
# so hard-coded paths in scripts and tests resolve. tools/env.sh switches tool paths when uname = Linux.
set -eux
mkdir -p /work/logs; exec >> /work/logs/bootstrap.log 2>&1
echo "$(date -u +%FT%TZ) bootstrap start"
while [ ! -f /work/SETUP_DONE ]; do sleep 10; done          # cloud-init apt step first (apt lock)
export DEBIAN_FRONTEND=noninteractive
sudo -E add-apt-repository -y ppa:kicad/kicad-10.0-releases
sudo -E apt-get update -y
sudo -E apt-get install -y --no-install-recommends \
  kicad kicad-symbols kicad-footprints kicad-packages3d \
  libreoffice-calc libreoffice-writer libreoffice-impress fonts-dejavu fonts-liberation fonts-noto-core \
  xvfb xauth ffmpeg imagemagick default-jre-headless \
  build-essential pkg-config libfontconfig1-dev libfreetype-dev libxkbcommon-dev libssl-dev \
  libgl1 libegl1 libxrender1 libxi6 libxxf86vm1 libxfixes3 libsm6 libice6 libx11-6 libxkbcommon0 libwayland-client0 \
  git rsync bc curl xz-utils unzip
# Blender 5.0.1 (same version as the Mac)
if [ ! -x /opt/blender/blender ]; then
  cd /opt && sudo curl -sSL https://download.blender.org/release/Blender5.0/blender-5.0.1-linux-x64.tar.xz -o /tmp/blender.tar.xz
  sudo tar -xJf /tmp/blender.tar.xz -C /opt && sudo mv /opt/blender-5.0.1-linux-x64 /opt/blender && sudo rm -f /tmp/blender.tar.xz
fi
# Freerouting (headless autorouter; Java 21)
sudo mkdir -p /opt/freerouting
[ -f /opt/freerouting/freerouting.jar ] || sudo curl -sSL https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar -o /opt/freerouting/freerouting.jar
# Mac-path mirror
sudo mkdir -p "/Volumes/Aditya ssd" && sudo ln -sfn /work/lab "/Volumes/Aditya ssd/Salt-Battery-Lab"
sudo chown -R ubuntu:ubuntu /work
# Python venv (uv-managed CPython 3.12, same pins as the Mac)
[ -x "$HOME/.local/bin/uv" ] || curl -LsSf https://astral.sh/uv/install.sh | sh
"$HOME/.local/bin/uv" venv /work/lab/.venv --python 3.12 --allow-existing
"$HOME/.local/bin/uv" pip install --python /work/lab/.venv/bin/python -r /work/lab/tools/ec2_build/requirements.txt
# KiCad's pcbnew module lives in the system python; expose it to the venv
echo "/usr/lib/python3/dist-packages" > /work/lab/.venv/lib/python3.12/site-packages/system_dist.pth || true
# Rust + CADCraft CLI
[ -x "$HOME/.cargo/bin/cargo" ] || curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
cd /work/cadcraft && "$HOME/.cargo/bin/cargo" build --release -p cadcraft-cli -j "$(nproc)" > /work/logs/cadcraft_build.log 2>&1 \
  && sudo install -m 755 target/release/cadcraft-cli /usr/local/bin/cadcraft-cli || echo "CADCRAFT BUILD FAILED (see cadcraft_build.log)"
# versions record
{ echo "blender: $(/opt/blender/blender --version 2>/dev/null | head -1)"; echo "kicad-cli: $(kicad-cli version 2>/dev/null)";
  echo "soffice: $(soffice --version 2>/dev/null)"; echo "python: $(/work/lab/.venv/bin/python -V)";
  echo "build123d: $(/work/lab/.venv/bin/python -c 'import build123d;print(build123d.__version__)' 2>&1)";
  echo "pcbnew: $(/usr/bin/python3 -c 'import pcbnew;print(pcbnew.Version())' 2>&1)";
  echo "cadcraft-cli: $(cadcraft-cli --version 2>&1)"; echo "java: $(java -version 2>&1 | head -1)"; echo "nproc: $(nproc)"; } > /work/logs/versions.txt
echo "$(date -u +%FT%TZ) bootstrap done"; touch /work/BOOTSTRAP_DONE
