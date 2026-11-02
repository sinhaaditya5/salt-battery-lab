# SCM-1 electrical test procedure (TP-E01…E06)

Run before any heated step (manual step E-01).

**Equipment:**
- bench supply 0–30 V / 1 A;
- precision voltage source or a calibrated 6½-digit DMM;
- 2 A electronic load;
- type-K calibrator (or ice point + boiling water);
- oscilloscope.

| ID | Test | Method | Pass |
|---|---|---|---|
| TP-E01 | Power-up | 24 V on J1 through a current-limited supply; measure +5V, +3V3, +3V3_ADC | 5.00 ± 0.10 V, 3.30 ± 0.05 V; idle current < 120 mA; LED_RUN blinks |
| TP-E02 | Cell-tap calibration | Apply 0.500, 1.500, 2.500 and 3.000 V on each tap pair in turn (string up to 12.4 V); record raw ADC and fit gain/offset per channel; store in flash | Residual ≤ ±2 mV per cell after calibration; channel isolation: 3.0 V on cell 1 changes cell 2 reading by < 1 mV |
| TP-E03 | Thermocouples | Calibrator at 0, 100, 200 and 300 °C on each input; open-circuit test | ±2 °C after cold-junction settling (10 min); open TC → MAX31856 OPEN bit and FAULT line low within 1 s |
| TP-E04 | Voltage trips | Ramp the tap-1 source through 2.95 V with TC inputs simulating 200 °C | FAULT latched at 2.95 ± 0.01 V; K1 NO-COM opens (DMM continuity); buzzer on; reset only with `R` after the cause is removed |
| TP-E05 | Current and over-current | 0.1, 0.5 and 1.0 A through J3 shunt path; then 0.2 A (> 181 mA limit) | Reading ±0.5 % ±1 mA; over-current FAULT at 181 ± 5 mA |
| TP-E06 | Heater interlock (hardware) | SSR output into a 24 V lamp. (a) firmware commands heat; (b) force TC4 > threshold with the MCU halted by debugger | (a) lamp on; (b) lamp off < 1 s **with firmware halted**; HEAT_FB reads back correctly |

Record results in `cell_record_template.csv` (columns `tp_e*`). **Any failure → no heated step.**
