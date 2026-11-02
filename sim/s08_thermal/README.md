# S8: Thermal and abuse model
**Question:**
- How hot does a block get at UPS and cycling rates?
- Is there an exothermic runaway chain?
- Which hazards remain?
**Model:**
- Lumped heat balance using S3 overpotential heat.
- A 2-D finite-difference cross-section of the block (cells, PP partitions, headspace) with natural convection.
- An abuse energy balance: stored energy vs the water's sensible and latent heat vs the case fire load.
**Results** (`out/s08_results.json`):
- 15-minute UPS discharge: max rise 2.8 K [C-119].
- If all stored energy became heat (adiabatic): +50 K, which stays below boiling [C-120].
- PP case fire load ~100 MJ vs 1.4 MJ stored [C-121].
**What remains:** H₂, case combustibility, leakage, Mn²⁺, and freezing or crystallisation.
**Limits:**
- Thermal properties are assumed.
- No reaction kinetics for external fire.
- No test data. UL 9540A would be the real test.
Run: `python run_s08.py`
