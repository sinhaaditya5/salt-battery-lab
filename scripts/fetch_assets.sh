#!/usr/bin/env bash
# Fetch third-party binaries and model weights that are not committed to git.
# Every download is verified against a pinned SHA-256. Re-running is a no-op if files are present and valid.
#
#   scripts/fetch_assets.sh            # everything
#   scripts/fetch_assets.sh models     # MACE-MP weights only (needed by sim/s05_atomistic)
#   scripts/fetch_assets.sh freerouting
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHAT="${1:-all}"

sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }

fetch() {  # fetch <url> <dest> <sha256>
  local url="$1" dest="$2" want="$3"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" && "$(sha256 "$dest")" == "$want" ]]; then
    echo "ok       ${dest#"$ROOT"/}"; return
  fi
  echo "fetch    ${dest#"$ROOT"/}"
  curl -fL --retry 3 --progress-bar -o "$dest.part" "$url"
  local got; got="$(sha256 "$dest.part")"
  if [[ "$got" != "$want" ]]; then
    rm -f "$dest.part"
    echo "SHA-256 mismatch for $url" >&2; echo "  want $want" >&2; echo "  got  $got" >&2; exit 1
  fi
  mv "$dest.part" "$dest"
  echo "verified ${dest#"$ROOT"/}"
}

models() {
  fetch "https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0/2023-12-03-mace-128-L1_epoch-199.model" \
        "$ROOT/tools/models/mace-mp-0-medium.model" \
        "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"
  fetch "https://github.com/ACEsuit/mace-foundations/releases/download/mace_mp_0b3/mace-mp-0b3-medium.model" \
        "$ROOT/tools/models/mace-mp-0b3-medium.model" \
        "2f2be696351ac9e94fbe01cdfb6f017679acdbd2db7645209ef55fec9826b012"
}

freerouting() {
  local os arch asset sums="$ROOT/tools/pcbtools/freerouting-cli-2.5.0-checksums.txt"
  case "$(uname -s)" in Darwin) os=macos ;; Linux) os=linux ;; *) echo "unsupported OS for freerouting-cli" >&2; return 1 ;; esac
  case "$(uname -m)" in arm64|aarch64) arch=arm64 ;; x86_64|amd64) arch=x64 ;; *) echo "unsupported arch" >&2; return 1 ;; esac
  asset="freerouting-cli-2.5.0-${os}-${arch}.tar.gz"
  local want; want="$(awk -v a="$asset" '{f=$2; sub(/^\*/,"",f)} f==a{print $1}' "$sums")"
  [[ -n "$want" ]] || { echo "no checksum for $asset in $sums" >&2; return 1; }
  fetch "https://github.com/freerouting/freerouting/releases/download/v2.5.0/$asset" "$ROOT/tools/pcbtools/$asset" "$want"
  mkdir -p "$ROOT/tools/pcbtools/freerouting-cli"
  tar -xzf "$ROOT/tools/pcbtools/$asset" -C "$ROOT/tools/pcbtools/freerouting-cli" --strip-components=0
  echo "unpacked tools/pcbtools/freerouting-cli/"
}

case "$WHAT" in
  all) models; freerouting ;;
  models) models ;;
  freerouting) freerouting ;;
  *) echo "usage: $0 [all|models|freerouting]" >&2; exit 2 ;;
esac
