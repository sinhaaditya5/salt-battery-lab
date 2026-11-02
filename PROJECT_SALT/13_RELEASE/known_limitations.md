# Known limitations (read before relying on any number)

## Evidence
1. **Nothing is measured.** No cell, electrode, ceramic or circuit board has been built. All performance numbers are [CALCULATED], [SIMULATED], [PUBLISHED], [VENDOR CLAIM] or [ASSUMPTION].
2. **Several sources were read only as abstracts, press releases or search snippets.** These include PS-001, PS-004, PS-005 and PS-006 (key cathode-basis numbers), and the CATL/BYD claims. No patent claims were read in full.
3. **Thermochemistry used to validate DFT was transcribed from standard tables (NBS/CRC) from memory.** It must be checked against the CRC Handbook before any of it is cited (`sim/s11_dft_chlorides/analyze.py` header).

## Models
4. **S12 build-up model.** Calibrated to seven reference cells (±15 %), but its inputs for immature chemistries (Na-Cl₂, Na-O₂, Ca, Mg, organic) are guesses within literature ranges. Their P10–P90 bands are model spread, not measured variability.
5. **S12 prices are wide assumptions.** β''-alumina price is the single most influential input ($15–200/kg), and no quote exists.
6. **S13a PyBaMM.**
   - The fast-charge evidence uses a *lithium* model (Chen2020, validated in its paper) as a physics benchmark.
   - The Na-ion parameter set failed our own validation gate (S02) and is shown as trend only.
   - The OKane degradation runs are 15 cycles; their extrapolation to 900–1,300 cycles is weak.
7. **S14 salt-cell model.**
   - It is ohmic-only and unvalidated.
   - Its 100 % utilisation and 97.6 % round-trip efficiency are upper bounds: particle growth, passivation and Na₆FeCl₈ formation are not modelled.
   - Its fast-charge conclusion (impossible at 12C) is robust, because it only needs the ohmic lower bound.
8. **S15 factory model.**
   - Scaling exponents, headcount, yields and energy intensities are assumptions.
   - The molten-salt capex rests on one company's feasibility study [VENDOR CLAIM].
9. **DFT (S11).**
   - PBE(+U)-D3 with GBRV ultrasoft pseudopotentials and screening-level settings.
   - Mixing GGA metals with GGA+U chlorides is not corrected (no fitted MP-style correction), which is why the U-scan is shown rather than one number.
   - The final-SCF crash of conda QE 7.6 after vc-relax is worked around by using BFGS-converged energies.
   - DOS/PDOS, band structures, the NaCl vacancy NEB and an ML-potential/MD study were **not run** in this session (inputs not prepared). They are listed as next computations.
10. **"BFT+U"** in the brief could not be identified as a method or software. Nothing was run under that name.

## Engineering
11. **CAD.** The S-cell design is a concept. Seal and gasket materials (graphite foil, glass, Ni 201 housing at cathode potential) are **unqualified candidates** (QT-02…QT-08). Tolerances are general (ISO 2768-mK) plus sealing-face flatness; no tolerance stack-up was done.
12. **SCM-1 PCB.** The schematic passes ERC with 0 violations, but the layout is an auto-placed, auto-routed **draft**: 37 unrouted connections, 178 clearance errors, schematic-parity field mismatches. Gerbers exist for review only. **Do not order boards.**
13. **Firmware.** Only the hardware-independent supervision core and the MAX31856 conversions are tested (host unit tests). The STM32 HAL, ADS131M08 and INA228 drivers are not written. Nothing has run on a target.
14. **Procurement.** Supplier names are real companies. Catalogue numbers and prices were **not** verified online for most items ("VERIFY" / "QUOTE REQUIRED"). The ARCI β''-alumina capability is unverified.

## Market
15. **Zero customer interviews.** TAM/SAM/SOM are from the earlier desk model (S10).
16. **Competitor data are company claims.**
