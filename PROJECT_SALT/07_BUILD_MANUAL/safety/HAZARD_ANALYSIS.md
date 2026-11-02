# Hazard analysis: S-cell R0 (salt-iron molten-salt cell) and the wider salt platform

**Design objective** (brief §10): no ignition and no uncontrolled propagation under the defined qualification tests. **We do not claim fire is impossible.** Molten sodium forms inside the charged cell, and the cell runs at 190–260 °C.

Scale: severity S1–S4 (S4 = injury or fire); likelihood L1–L4 before controls. Residual risk must be L1 or L2 with S ≤ 3 before a charged cell exists.

## 1. Hazard register (HAZOP-style, lab scale)

| # | Hazard / cause | Consequence | S | L | Controls (design · procedure · PPE) | Residual | Verification |
|---|---|---|---|---|---|---|---|
| H1 | **Ceramic (β''-alumina) fracture** in a charged cell: thermal shock, mechanical stress | Molten Na meets NaAlCl₄: **2Na + NiCl₂/FeCl₂ → NaCl + metal** (exothermic but self-limiting in ZEBRA), and 3Na + NaAlCl₄ → 4NaCl + Al (1.58 V reaction). Local heating. Cell fails short (benign ZEBRA failure mode [PUBLISHED, general]) | 3 | 2 | ramp ≤ 2 °C/min (firmware F_RAMP + procedure); 0.2–0.4 mm wick compression; ceramic inspection A-04; steel drip tray with sand; furnace in a fume-extracted enclosure | S3·L1 | QT-03 thermal cycling; UL 9540A-type cell test later |
| H2 | **Seal or casing breach** while hot | NaAlCl₄/AlCl₃ + air moisture → **HCl gas**; Na + air → Na₂O/NaOH smoke; possible Na fire | 4 | 2 | He-leak acceptance ≤ 1e-8 (C-03, D-08); operation in an Ar glovebox or a sealed furnace with extraction; HCl detector; Class D extinguisher + dry sand; **never water** | S3·L1 | QT-02, QT-04, QT-07 |
| H3 | **Overcharge** above ~3.05 V | 2NaAlCl₄ + Ni → NiCl₂ + 2Na + 2AlCl₃: consumes electrolyte; AlCl₃ vapour raises pressure | 3 | 2 | cycler limit 2.75 V; SCM-1 trip 2.95 V (latched, opens the cycler interlock); hardware relay fail-safe | S2·L1 | TP-E04; firmware tests (19/19 pass) |
| H4 | **Over-discharge** below ~1.58 V | NaAlCl₄ + 3Na → Al + 4NaCl: irreversible electrolyte loss | 2 | 2 | cycler 1.80 V; SCM-1 trip 1.65 V (READY state) | S2·L1 | firmware tests |
| H5 | **Heater runaway** (stuck SSR, controller fault) | > 300 °C: seal glass softening, ceramic stress, Na vapour pressure | 4 | 2 | three independent layers: (1) MAX31856 HI threshold → **hardware AND gate** removes SSR drive without firmware; (2) firmware latch; (3) **bimetal cut-out 300 °C + E-stop in series with mains**, off-board | S3·L1 | E-03 interlock test with firmware halted |
| H6 | **AlCl₃ handling** (B-04) | Corrosive; violent with water → HCl | 3 | 3 | glovebox only; small batches (< 20 g); face shield at transfers | S2·L1 | SOP sign-off |
| H7 | **Ni / Fe powders** | Ni: sensitiser, Carc. 2; fine Fe can be pyrophoric | 3 | 2 | glovebox; no high-energy milling; waste as heavy metal | S2·L1 | — |
| H8 | **Short circuit** (external) | Up to several A from a small cell: heating of the leads | 2 | 2 | cycler current limit; SCM-1 over-current trip (181 mA); insulated bolts and sleeves (QT-08) | S1·L1 | TP-E05 |
| H9 | **Thermocouple shorting cells** through a common ground | Uncontrolled discharge path | 2 | 3 | **ungrounded-junction TCs only** (silkscreen and manual) | S1·L1 | TP-E02 |
| H10 | **Burns** from the 200 °C hardware | Injury | 3 | 3 | tongs; heat-resistant gloves; two-person rule | S2·L2 | training |
| H11 | **Disassembly of a charged cell** | Na metal exposure | 4 | 2 | always discharge first (H-01); quench with IPA in the glovebox | S3·L1 | log |
| H12 | **Waste** | HCl on hydrolysis; Ni waste | 2 | 3 | slow hydrolysis in a fume hood; licensed contractor | S1·L2 | waste log |

## 2. Chemistry-level hazards across the platform (for product decisions)

- **Thermal runaway:** no organic electrolyte in S01–S03, so no solvent fire. The stored chemical energy, including molten Na, is still released if the ceramic fails. ZEBRA passed crash and fire tests historically, and UL 9540A large-scale data exist for Na–NiCl₂ (Battcon 2021, not read) [PUBLISHED].
- **Gas:** no H₂ or O₂ in normal operation (no water). HCl only after a breach plus moisture. Na–Cl₂ (S04) holds Cl₂ by design, which is unacceptable for indoor use.
- **Toxicity:** Ni (S01/S02) is the main chronic hazard. The Fe variant (S03) removes 90 % of it.
- **Transport:** a sodium-metal-containing battery falls under **UN 3292** and needs **UN 38.3** testing [PUBLISHED PS-024]. Discharged-state shipping, where the Na is all in NaCl, is a known ZEBRA advantage, but the classification must be confirmed with a DG consultant [UNVERIFIED].

## 3. Standards register (applicability: verify the current edition before use)

| Standard | Scope | Applies to | Status in this package | Label |
|---|---|---|---|---|
| IEC 62984-1/-2/-3:2020 | High-temperature secondary batteries; part 3 = Na-S & Na-NiCl₂ performance, ≤1,500 V, mobile/stationary; ED2 of part 3 in development | S01–S03 product | Primary product standard to design to | [PUBLISHED PS-034] |
| UL 9540A (current edition: verify) | Thermal-runaway fire-propagation test method for ESS | stationary product | Needed for NFPA 855 / IFC siting | [PUBLISHED, existence]; edition [UNVERIFIED] |
| NFPA 855 (2023/2026) and IFC (2021/2024) | ESS installation; threshold quantity for Na-NiCl₂ 20 kWh, 70 kWh if UL 1973-listed | indoor UPS/telecom | Gives **no** advantage over Li-ion in threshold terms | [PUBLISHED PS-015/016] |
| UL 1973 | Stationary batteries | product | Listing needed for the 70 kWh threshold | [UNVERIFIED edition] |
| UN Manual of Tests and Criteria 38.3; UN 3292 / 3551 / 3552 | Transport | cells and modules | Na-metal cells: UN 3292 | [PUBLISHED PS-024] |
| IEC 62619 / IEC 62620 | Industrial secondary Li batteries | **not** Na-MCl₂ (lithium only); relevant to the Na-ion alternative N02 | reference | [UNVERIFIED applicability to Na-ion] |
| IS 16046 (India; IEC 62133 adoption) and BIS CRS | Portable sealed cells | consumer/laptop (not this product) | n/a for R0 | [UNVERIFIED] |
| AIS-156 / AIS-038 Rev 2 (India); UN ECE R100; SAE J2464; FMVSS 305 | EV traction battery safety | EV (out of scope by verdict) | listed for completeness | [UNVERIFIED editions] |
| IEC 60952 (aircraft), DO-311A, MIL-PRF / MIL-STD-810 | Aviation / defence | out of scope | listed only | [UNVERIFIED] |
| India CEA (Technical Standards / Safety) regulations for BESS; TEC GRs for telecom batteries | grid / telecom | first market | must be read before any India pilot | [UNVERIFIED] |

**No certification, listing or exemption is claimed for anything in this package.**
