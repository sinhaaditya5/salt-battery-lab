# Electronics: SCM-1 salt-cell test monitor (designed for the S-cell chemistry and voltage)

| Item | Status |
|---|---|
| Schematic (`kicad/`, `schematics/`) | 145 parts, 94 nets; **ERC 0 violations** (MAX31856 pin types corrected to datasheet: SDO tri-state, FAULT open-drain, in `scm_pcb.kicad_sym`) |
| PCB (`pcb/`) | 4-layer, 110 × 75 mm; auto-placed, auto-routed **DRAFT**: 1,703 tracks, 37 unrouted connections, 178 clearance errors → **not for fabrication** |
| Gerbers / drill / pick-and-place (`gerbers/`) | exported from the draft, **for review only** |
| BOM (`bom/`) | grouped, with manufacturer part numbers |
| Firmware (`firmware/`) | supervision core + MAX31856 driver + main loop. `make test`: **19/19 core checks, 0 driver failures, main loop syntax-clean under -Werror**. HAL, ADS131M08 and INA228 drivers not written |
| Electrical test procedure | `07_BUILD_MANUAL/acceptance_tests/ELECTRICAL_TEST_PROCEDURE.md` (TP-E01…E06) |

**Design basis** (`params/scell_params.py`, generated `firmware/limits.h`):
- 1.65 / 2.95 V cell trips (inside the 1.58 / 3.05 V side reactions);
- 290 °C hardware thermocouple trip;
- 2 °C/min ramp limit;
- 181 mA (40 mA/cm²) over-current trip.
