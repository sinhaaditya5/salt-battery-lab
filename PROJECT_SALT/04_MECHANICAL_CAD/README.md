# Mechanical CAD (S-cell R0)

- **Native parametric source:** `native_sources/make_scell.py` (build123d / OpenCascade); every dimension comes from `native_sources/scell_params.py`.
- **Drawing SB-SC-001:** CADCraft A2, 2:1 section, plan, item list, loading table, notes.
- **Outputs:**
  - STEP (assembled + exploded);
  - STL per part (visual and jig use only);
  - GLB;
  - DXF/PDF/PNG drawing;
  - BOM-linked part list with material, tolerance and qualification test per item (`cell/scell_r0_partlist.csv`).

**Status:** concept. Tolerances are general (ISO 2768-mK) plus sealing-face flatness/Ra. No tolerance stack-up. Seal materials are unqualified.

Earlier aqueous-track CAD (R0/R1 block, 48 V tray, UPS cabinet) remains in `cad/out/` and `DELIVERABLES/3_cad_3d`.
