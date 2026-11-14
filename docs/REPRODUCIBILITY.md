# Reproducibility

## Tiers

| Tier | What you get | Needs | Time |
|---|---|---|---|
| **1. Checks** | Integrity gate, core tests, firmware tests | Python 3.12, a C compiler | ~2 min |
| **2. Models** | Re-run S1–S16 analyses and charts | + `tools/ec2_build/requirements.txt` (PyBaMM, MACE, CHGNet, pymatgen, ASE) and `scripts/fetch_assets.sh models` | 15 min – 1 h |
| **3. Full build** | CAD, drawings, renders, PCB, spreadsheets, documents, video | + Blender 5.0.1, KiCad 10, CADCraft, LibreOffice, Octave, ffmpeg | ~1 h on a 32-vCPU host |
| **4. DFT** | New Quantum ESPRESSO jobs | AWS account, QE 7.6 (conda-forge), budget approval | hours, costs money |

## Lab path

The scripts use the absolute lab root `/Volumes/Aditya ssd/Salt-Battery-Lab`. To run them from any clone:

```bash
make link     # = sudo ln -sfn "$PWD" "/Volumes/Aditya ssd/Salt-Battery-Lab"
```

On Linux this creates `/Volumes/Aditya ssd/` as an ordinary directory. The EC2 build host (`tools/ec2_build/bootstrap.sh`) and CI (`.github/workflows/ci.yml`) do the same thing.

## Environment

`tools/env.sh` points every cache at the lab drive: pip, uv, Hugging Face, Torch, Matplotlib, Blender and micromamba. It also locates Blender, KiCad, CADCraft and LibreOffice:

```bash
source tools/env.sh
```

| Lock file | Purpose |
|---|---|
| `requirements/ci.txt` | Minimal pinned set for the core tests |
| `tools/ec2_build/requirements.txt` | Full pinned lock used on the EC2 x86 build host (121 packages, Python 3.12) |

## Third-party assets

Model weights and binaries are not committed. Fetch them with SHA-256 verification:

```bash
scripts/fetch_assets.sh            # MACE-MP-0 / 0b3 weights + Freerouting CLI 2.5.0
```

Papers and datasheets are cited, not redistributed: see [`research/REFERENCES.md`](../research/REFERENCES.md).

## Rebuild

```bash
./run_all.sh --fast   # reuse ML-potential runs and renders
./run_all.sh          # full
```

`run_all.sh` writes per-step logs to `work/run_all_logs/` and console snapshots to `DELIVERABLES/11_screenshots/`. At the end it regenerates `DELIVERABLES/9_data/TEST_REPORT.md`.

## EC2 build host (heavy work)

Heavy jobs ran on a spot x86 host so they stay off the laptop: Blender, KiCad, CADCraft, LibreOffice, Octave and pytest. The tooling is in `tools/ec2_build/`:

```bash
tools/ec2_build/ec2_build.sh push        # rsync --update the lab to /work/lab
tools/ec2_build/ec2_build.sh bootstrap   # install the toolchain (idempotent)
tools/ec2_build/ec2_build.sh bg <name> "<cmd>"
tools/ec2_build/ec2_build.sh pull
```

## DFT on AWS

`sim/s06_dft_ec2/launch.sh` starts a Graviton (c8g) or x86 spot instance. It applies a hard stop time and a dollar cap, set per job with `S06_HARD_HOURS`, `S06_CAP_USD`, `S06_ITYPE` and `S06_MAXPRICE`. `sim/s11_dft_chlorides/ec2/ec2_s11.sh push | status | pull` drives the S11 campaign, and `sim/s06_dft_ec2/terminate.sh` cleans up. QE scratch (`*.save/`, `*.wfc*`, `tmp/`) is git-ignored; inputs, outputs and parsed JSON are committed.

## Known limitations

See [`PROJECT_SALT/13_RELEASE/known_limitations.md`](../PROJECT_SALT/13_RELEASE/known_limitations.md). In particular:

- The SCM-1 layout is a draft and is not for fabrication.
- The PyBaMM sodium DFN fails independent validation.
- No electrochemical data exist.
