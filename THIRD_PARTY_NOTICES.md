# Third-party notices

The [`LICENSE`](LICENSE) of this repository covers original work only. The components below belong to their authors and keep their own licences.

## Bundled in the repository

| Component | Location | Source | Licence / terms |
|---|---|---|---|
| GBRV ultrasoft pseudopotentials v1.x (PBE) | `tools/pseudo/gbrv/`, `tools/pseudo/gbrv_pbe_v1.5.tar.gz` | Garrity, Bennett, Rabe, Vanderbilt, *Comput. Mater. Sci.* 81, 446 (2014); <https://www.physics.rutgers.edu/gbrv/> | GPL, as distributed by the GBRV authors |
| Figure 4 of Chayambuka *et al.*, *Electrochim. Acta* 404 (2022) 139764 | `sim/s02_pybamm_validation/ref/fig4_p6_0_Im7.jpg` | <https://doi.org/10.1016/j.electacta.2021.139764> | © the authors / publisher; reproduced only as validation data for digitisation |
| Freerouting release checksums | `tools/pcbtools/freerouting-cli-2.5.0-checksums.txt` | <https://github.com/freerouting/freerouting> | GPL-3.0 (checksums only; no binary is bundled) |

## Fetched on demand (not committed)

`scripts/fetch_assets.sh` downloads these and checks each against a pinned SHA-256.

| Component | Destination | Source | Licence |
|---|---|---|---|
| MACE-MP-0 medium | `tools/models/mace-mp-0-medium.model` | <https://github.com/ACEsuit/mace-mp> | MIT (see upstream) |
| MACE-MP-0b3 medium | `tools/models/mace-mp-0b3-medium.model` | <https://github.com/ACEsuit/mace-foundations> | See upstream model card |
| Freerouting CLI 2.5.0 | `tools/pcbtools/freerouting-cli/` | <https://github.com/freerouting/freerouting/releases> | GPL-3.0 |

## Referenced, not redistributed

Copyrighted papers, vendor datasheets and the COMSOL application note used during the study are **not** in this repository. Citations and download links are in [`research/REFERENCES.md`](research/REFERENCES.md).

## Software used to generate outputs

The outputs in this repository were produced with Python 3.12 and its scientific stack. That includes NumPy, SciPy, Matplotlib, pymatgen, ASE, PyBaMM, MACE, CHGNet, build123d/OCP, ezdxf, python-docx, python-pptx and openpyxl; the full pinned list is in `tools/ec2_build/requirements.txt`. The other tools were Quantum ESPRESSO 7.6, Blender 5.0.1, KiCad 10, CADCraft, LibreOffice and GNU Octave. Each is used under its own licence. None of them is redistributed here.
