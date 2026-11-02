# Automation, PLC, vision and traceability (concept)

**Rule (brief §9):** do not automate a step before its parameters are validated. Stage A is manual. Stage B automates only material handling, filling and formation data capture.

| Layer | Choice (concept) | Why |
|---|---|---|
| Machine control | IEC 61131-3 PLCs, one per cell or station; ISA-88 state model (Idle/Running/Held/Aborted) per station | Standard and auditable |
| Safety | Separate SIL-rated safety PLC for furnaces and melt stations: hardwired E-stop, over-temperature, HCl gas → isolate and extract | Heaters and HCl are the dominant hazards (HAZARD_ANALYSIS H2/H5) |
| Communication | OPC UA from stations to the MES; EtherNet/IP or PROFINET at field level | Vendor-neutral data model |
| Traceability | 2-D DataMatrix laser-marked on the anode housing; lot genealogy (salt lot, Fe lot, disc serial → cell) in the MES | Recalls and failure analysis |
| Machine vision | Ceramic-disc crack inspection (back-lit, plus dye penetrant on samples); granule-bed level check before closure | Cracks are the most dangerous latent defect (H1) |
| Robotics | Only for hot-cell handling (furnace load/unload) and melt filling, after Stage B data exist | Burns and HCl exposure |
| Formation | Cycler data → MES; automatic hold of cells whose first-charge plateau or ASR fails G-limits | Yield learning |

The SCM-1 firmware state machine (`05_ELECTRONICS/firmware`) is the lab-scale prototype of the station safety logic: latched faults, a hardware heater interlock, and a fail-safe cycler interlock.
