# Application-specific architectures (brief §12)

**No single physical cell serves all ten markets.** For each market the table gives the best candidate from the S12 matrix and states whether any salt-derived chemistry is credible.

| Application | Critical requirement | What it needs (cell level) | Best salt-derived option (S12) | Fit | Cell format if pursued |
|---|---|---|---|---|---|
| Drone | Wh/kg, W/kg | ≥ 300 Wh/kg, ≥ 3C | none (N08 259 P50, low power) | **No** | – |
| Laptop | Wh/L, safety, cycles | ≥ 250 Wh/kg, ≥ 650 Wh/L | N01/N03 (~176 Wh/kg) | Weak (bulky) | small pouch |
| UPS (minutes) | power, reliability | 15-min rate (4C), 10–15 y | N02/N04 Na-ion; S01/S03 too slow and too costly | Na-ion: yes. Salt-iron: **no** (C/5–1C) | prismatic Na-ion |
| Telecom backup (hours) | hot sites, theft, 10+ y | C/5–C/2, 2–8 h, 45–55 °C ambient | **S03/S01** (temperature-indifferent, non-flammable) | **Technically yes; economically no today** | planar or tubular 2.5 V cells, 48 V modules (20 cells) |
| Data centre | safety codes, footprint | ≥ 100 Wh/L, UL 9540A | N02 / S01 | Na-NiCl₂ has no NFPA 855 threshold advantage (20/70 kWh) | – |
| Grid storage | LCOS, cycles | ≥ 6,000 cycles, ≤ $0.05/kWh delivered | N02 (LCOS $0.05–0.07); Fe-air for multi-day | Na-ion only | large prismatic |
| Passenger EV | Wh/kg, fast charge, safety | ≥ 250–360 Wh/kg, 4–12C | none (S13: 3.8 MW / 11.7C needed) | **No** | – |
| Heavy truck / bus | energy, life | ≥ 200 Wh/kg pack | none; ZEBRA powered buses historically at ~100 Wh/kg | No (mass) | – |
| Robotics | power, compact | ≥ 5C, ≥ 200 Wh/kg | N04 NVPF (high power, 161 Wh/kg) | Weak | cylindrical |
| Defence | temperature range, shock | −40…+60 °C, MIL-STD-810 | S01 (temperature-indifferent) or N02 | Niche | – |
| Aerospace | Wh/kg, certification | ≥ 300 Wh/kg, DO-311A-type | none | **No** | – |

**Platform statement.** The only coherent salt "platform" is the β''-alumina family:
- Na metal | Na⁺-ceramic | interchangeable cathode, i.e. MCl₂ (S01–S03), S (N10), or in future Cl₂ or intercalation hosts.
- It shares the ceramic separator, the Na anode and the heated thermal enclosure. It is prior art (the "sodium-beta battery" family), not an invention.
- It serves stationary, hot-site and heavy uses only.
