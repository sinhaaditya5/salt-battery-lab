# Changelog

All notable changes to this lab are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow the study's release history (`PROJECT_SALT/13_RELEASE/version_history/CHANGELOG.md`).

## [Unreleased]

### Added
- Public repository scaffolding: README with gallery and pipeline diagram, `LICENSE` (all rights reserved), `THIRD_PARTY_NOTICES.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff`.
- CI on GitHub Actions: an integrity gate (secrets, file sizes, JSON/CSV/Python validity, shell syntax), firmware host tests with a `limits.h` drift check, and core pytest suites.
- `scripts/fetch_assets.sh`: fetches MACE-MP weights and Freerouting, verified by SHA-256, in place of committing third-party binaries.
- `scripts/check_repo.py`, `Makefile`, `pyproject.toml`, `requirements/ci.txt`, `.editorconfig`, `.gitattributes`.
- `docs/ARCHITECTURE.md`, `docs/REPRODUCIBILITY.md`, `research/REFERENCES.md`.

### Changed
- The original lab README moved to `docs/LAB_NOTEBOOK.md`.

### Removed
- Third-party papers, datasheets, model weights and binaries are no longer committed. `research/REFERENCES.md` and `scripts/fetch_assets.sh` replace them.
- Regenerable intermediates (`video/tmp/`, `drawings/out/tmp/`, host firmware test binaries, the LibreOffice profile).

### Security
- The public history was started fresh. It contains no credentials.

## [1.1.0] - 2026-11-03

### Added
- S11 completed on EC2 (c8g.8xlarge spot): NiCl₂ relaxations, a 24-job U-scan, a 12-job FM/AFM stage, a 6-job PDOS stage, a band-gap parser and 8 S11 tests.
- D3 P1 cell and SM-48T 48 V module, D4 thermal model (S16), D5 SC-UPS-1 cabinet: STEP, part lists, CADCraft drawings SB-SM-001 / SB-TM-001 / SB-UPS-001.
- Blender renders and turntable of the salt designs; diagrams ds1–ds5; MATLAB/Octave stem scripts.
- `SaltIron_Engineering_Model.xlsx` (live formulas, LibreOffice-verified); complete technical record and deck.
- EC2 x86 build host (`tools/ec2_build/`), so heavy work runs off the laptop.

### Fixed
- The S11 runner re-ran jobs that had already converged.

Conclusions unchanged: **Outcome B**.

## [1.0.0] - 2026-11-02

### Added
- **Project Salt** second brief: 30-architecture feasibility matrix (S12), founder-target tests (S13), PyBaMM fast charge and degradation (S13a), salt-iron cell model (S14), factory scenarios and tornado (S15).
- DFT+U on Na / NaCl / Cl₂ / Fe-Co-Ni chlorides (S11).
- S-cell R0 CAD and drawing SB-SC-001; SCM-1 KiCad board and firmware core; procurement BOM; build manual; hazard analysis.
- Executive verdict: **Outcome B**. No salt-derived chemistry meets the combined founder specification.

## [0.4.0] - 2026-11-02

### Added
- Narrated explainer video with subtitles; YC answers v3; report, one-pager, outreach pack, data room; `run_all.sh` (fast path verified: 28 tests pass).

## [0.3.0] - 2026-11-02

### Added
- Investor deck (28 slides, linted with 0 problems); chart and diagram QA fixes; DFT restart after a spot reclaim.
- Tests (25 pass), claims linter, simulation READMEs, financial model (LibreOffice-verified), interim test report.
- Diagrams, claims ledger, startup decision memo (no-go as framed; conditional sprint).

## [0.2.0] - 2026-11-02

### Added
- S7 build-up, S10 market, chemistry matrix, IDEA_v2 with the R1 target spec and kill criteria.
- Phase 2 research (164 sources), S9 TEA, YC answers v2 (corrected IFC threshold, honest cost finding).
- S2 PyBaMM validation (fails its voltage gate; documented), S3 R1 DFN + Monte Carlo, S4 gas/water budget, S8 thermal/abuse, R1 parameters and design, decisions log.

## [0.1.0] - 2026-11-02

### Added
- Lab layout, verified copy of the R0 reference-cell kit (50/50 SHA-256), `tools/env.sh`, YC W27 application drafts.
- S1 kit re-run (9/9), S5 structures + uMLIP relax, S6 EC2 DFT+U package (QE 7.6, conda-forge), parameters v0.

[Unreleased]: https://github.com/sinhaaditya5/salt-battery-lab/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/sinhaaditya5/salt-battery-lab/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/sinhaaditya5/salt-battery-lab/compare/v0.4.0...v1.0.0
[0.4.0]: https://github.com/sinhaaditya5/salt-battery-lab/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/sinhaaditya5/salt-battery-lab/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sinhaaditya5/salt-battery-lab/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sinhaaditya5/salt-battery-lab/releases/tag/v0.1.0
