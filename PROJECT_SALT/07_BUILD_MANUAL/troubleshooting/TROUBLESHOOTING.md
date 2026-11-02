# Troubleshooting (S-cell R0)

| ID | Symptom | Likely cause | Check | Action |
|---|---|---|---|---|
| T-01 | Glovebox H₂O rises during B-04 | AlCl₃ hydrolysis products, or a leaking glove | analyser trend; glove inspection | Stop; regenerate purifier; replace glove |
| T-02 | NaAlCl₄ grey or black | metal or carbon contamination; crucible attack | crucible inspection | Discard; use a new glassy-carbon or quartz vessel |
| T-03 | First charge jumps to 2.75 V with no plateau | No Na wetting on the anode face, so no ionic path; or melt not infiltrated | EIS: very high bulk R; melt mass (D-07) | Cool, disassemble in the box; add carbon wetting layer (D-04); re-infiltrate |
| T-04 | Plateau at ~2.58 V only (no 2.35 V) | Fe passivated (oxide); S additive missing | XRD of cathode | Check Fe O-content; confirm FeS added; re-make granules |
| T-05 | Capacity fades fast (> 1 %/cycle) | Fe particle growth / pulverisation; NaCl coarsening | SEM after test | Lower operating T; finer Fe; check Ni additive (PS-005 reports Ni mitigates Fe pulverisation) |
| T-06 | OCV drifts down at rest | Internal leak; electronic leakage through the glass seal or ring | Insulation test hot (QT-08) | Replace seal; check sleeves and washers |
| T-07 | Seal leak after heating | CTE mismatch; ramp too fast | QT-03 log | New glass; slower ramp |
| T-08 | SCM-1 FAULT F_STALE | SPI/I2C bus error; MAX31856 not responding | scope on SPI; FAULT pin | Check CS lines and pull-ups; re-seat TC connectors |
| T-09 | SCM-1 FAULT F_RAMP during heat-up | furnace PID too aggressive | furnace log | Reduce furnace gain; SCM-1 setpoint ramps at 2 °C/min |
| T-10 | HCl smell outside the box | breach plus moisture | detector | **Evacuate, ventilate, follow the lab emergency plan** |
