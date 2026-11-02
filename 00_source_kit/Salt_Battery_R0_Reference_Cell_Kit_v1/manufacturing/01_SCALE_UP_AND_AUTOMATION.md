# Manufacturing architecture — staged and conditional

## Important engineering boundary

The R0 paper uses a research-cell process: powder synthesis, drop-casting onto small carbon-paper discs, filter-paper separator and a split test fixture. This does **not** establish a roll-to-roll industrial process. The carbon-paper/drop-cast construction is a laboratory reference and may be unsuitable for high-volume manufacture. Industrial coating, current collector, separator, electrolyte filling and cell format must be re-engineered and requalified after electrochemistry is reproduced.

## Stage 1 — laboratory build (1–10 g active-material research scale)

| Process station | Equipment | Process data to capture | Output / QC |
|---|---|---|---|
| Precursor solution | Chemical fume hood, calibrated balance, glass reactor, overhead stirrer, metering syringe/pump | Chemical lot, concentration, flow trace, temperature, pH, time | Logged precursor batch |
| Solid/liquid separation | Chemical-compatible centrifuge and tubes | Rotor, RCF, time, sample mass | Washed precursor; mass/yield |
| Washing/drying | DI water wash, solvent-compatible vacuum oven | Wash volume, conductivity/pH endpoint, drying profile | Dried Mn3O4 precursor |
| Sodium insertion | Mortar/pestle or qualified low-contamination mixer; calibrated tube furnace | NaOH:Mn3O4 ratio, furnace ramp/soak, air atmosphere, crucible ID | Candidate Na-birnessite powder |
| Powder release | XRD, ICP-OES/MS, TGA, SEM | Sample ID, calibration, uncertainty | Released/rejected batch |
| Electrode process | Analytical balance, controlled slurry mixer/sonicator, drop-casting or controlled film applicator, vacuum oven | Solids fraction, solvent, mixing energy/time, active loading, area, drying | Electrode coupon; mass and resistance |
| Cell assembly | Qualified R&D split-cell fixture, separator/electrolyte dispenser, assembly jig | Fixture ID, separator grade, electrolyte volume, stack thickness, pressure protocol | Research cell |
| Electrochemical test | Potentiostat, battery cycler, temperature/gas monitoring as approved | Voltage, current, temperature, pH, gas observation, mass denominator | Raw cycler data and test report |

## Stage 2 — pilot process development (0.1–1 kg powder campaigns; only after Gate R0)

This is a process-development target, not a claim that the current chemistry has a qualified pilot recipe.

1. Replace hand dosing with a jacketed, instrumented stirred reactor and calibrated chemical dosing skid.
2. Replace batch centrifugation if possible with a qualified filter/centrifuge train; validate particle loss and washing efficiency.
3. Define controlled drying and powder conditioning; record humidity exposure and powder moisture.
4. Use batch furnace or continuous calciner only after phase, oxygen exposure, residence time and morphology have been mapped.
5. Establish powder classification, contamination controls, ICP release limits and lot traceability.
6. Develop a reproducible electrode slurry using measured wetting/adhesion. The source paper does not publish all full-cell slurry details; the pilot formulation is a new process and must be labelled R0-D or a new revision.
7. Move from drop-cast discs to small slot-die or doctor-blade coating only after an electrode/current-collector pair is selected. Map loading, thickness, porosity, adhesion, drying and rate performance.
8. Qualify separator, cell hardware, electrolyte dispensing, sealing, formation and end-of-line tests.
9. Run at least three independent pilot lots and compute mass yield, process yield, scrap, energy use, water use, labour time and batch cycle time.

### Pilot equipment families

- Metered chemical dosing skid and glass-lined/compatible reactor.
- Filtration or centrifuge system with wash-water monitoring.
- Solvent-compatible drying system with explosion/fire controls where ethanol is used.
- Calibrated batch furnace with exhaust and temperature uniformity records.
- Powder mill/classifier with dust extraction.
- Vacuum or planetary slurry mixer; rheometer/viscometer.
- Small slot-die/doctor-blade coater and controlled dryer.
- Thickness/mass-loading gauge and electrode resistance meter.
- Precision cutter/punch, cell assembly station and electrolyte dispenser.
- Formation cycler, EIS, thermal monitoring and approved abuse-test capability.
- LIMS/MES database, barcode/QR traceability and electronic batch record.

## Stage 3 — industrial manufacturing architecture (conditional)

Do not purchase or design a GWh line before the final chemistry, cell format, electrode process and safety design are frozen.

A mature production route would typically require:

1. Incoming raw-material inspection and lot quarantine.
2. Automated powder dosing and batch/continuous reaction systems.
3. Filtration, washing, drying, classification and closed-loop process control.
4. Automated slurry preparation and rheology control.
5. Roll-to-roll coating/drying, calendering and slitting—only if the selected electrode architecture supports it.
6. Electrode stacking/winding and cell enclosure integration.
7. Electrolyte filling or solid electrolyte integration; vacuum sealing where appropriate.
8. Formation, aging, EOL grading and impedance screening.
9. Module/pack assembly, BMS, thermal controls and final functional tests.
10. Automated traceability, process capability monitoring, field-failure feedback and recycling.

R0's carbon-paper research electrode and drop-casting method are not a validated continuous-coating line. Do not assume that the same manufacturing process scales directly.

## Automation/control architecture

- Safety PLC: hard interlocks for fume hood/exhaust status, furnace over-temperature, pump limits, spill containment, door interlocks, cycler voltage/current cutoffs and emergency stop.
- Process PLC: dosing, mixing, furnace profile, dryer profile and equipment sequencing.
- Sensors: mass, temperature, flow, pH/conductivity, humidity, pressure where relevant, thickness, resistance and vision inspection.
- Supervisory layer: SCADA/HMI with role-based access and immutable event logs.
- Data layer: recipe version, operator, material lot, equipment calibration, raw sensor streams, deviations and disposition.
- MES/LIMS: unique powder/electrode/cell identifiers, genealogy and test records.
- Machine vision: coating pinholes, cracks, edge defects, contamination and label/traceability inspection; model outputs require validated reject thresholds.

## Scale-up gate metrics

No pilot/industrial scale decision without measured:

- isolated powder yield and impurity rate;
- active-material composition and hydration consistency;
- electrode loading and thickness variation;
- electrode adhesion and sheet resistance;
- formation yield and cell rejection rate;
- capacity/energy distribution across at least three lots;
- energy and water per kg active material;
- direct labour, batch time and maintenance;
- waste treatment and recovery costs;
- supplier qualification and dual-source resilience.
