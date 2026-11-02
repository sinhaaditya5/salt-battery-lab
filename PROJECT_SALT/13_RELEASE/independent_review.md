# Review status: **NOT independent**

No third party has reviewed this package. What follows is an *internal adversarial review* by the same AI system that produced the work, written to make an external reviewer's job faster. **It must not be presented as an independent review.**

## Questions an external reviewer should attack first
1. **Calibration circularity (S12).** Were the build-up inputs tuned to hit the published cells? Partly yes: the input ranges were chosen from typical values and accepted once the calibration error was within ±15 %. A reviewer should re-run with their own inputs.
2. **Is the 360 Wh/kg "no" robust?** It rests on cathode-level ceilings (≈3.1–3.3 V × 120–185 mAh/g for Na hosts). A sodium cathode at ≥ 750 Wh/kg-CAM with stable cycling would overturn it. None is known to us; anionic-redox Na oxides should be checked.
3. **Salt-iron economics.** S15 uses one vendor's capex for a first plant. A purpose-designed planar line could be far cheaper. This is the largest single uncertainty behind "4–5× Na-ion".
4. **PNNL basis.** Our reading of PS-005/PS-006 Wh/kg as material-basis values (not cell) comes from abstract wording. Read the papers.
5. **Fire-code statement.** The NFPA 855 / IFC thresholds for Na-NiCl₂ (20/70 kWh) come from secondary documents; check the adopted edition.
6. **Patent FTO.** The R0 recipe sits inside Battelle US10615407B2's claim space (Fe + S additive + NaCl, discharged assembly). Research use is generally fine; anything commercial needs counsel.

## Requested independent reviewers (none engaged)
- An electrochemist with ZEBRA or Na-β experience (ideally ex-FZSoNick, Fraunhofer IKTS or PNNL).
- A battery cost-modelling analyst (BatPaC familiarity).
- A fire-protection engineer (NFPA 855).
