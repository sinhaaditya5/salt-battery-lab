# Stage C — Industrial scenarios (1 MWh, 10 MWh, 100 MWh, 1 GWh per year)

**Source:** `10_ECONOMICS/factory_capex/s15_results.json` (model `sim/s15_factory/factory.py`). These are **scenario capacities, not targets**. All inputs are [ASSUMPTION] except the Altech molten-salt capex anchor [VENDOR CLAIM PS-032].

| Line | Scale (MWh/yr) | Capex | $ per kWh/yr | Headcount | Power (MWh/yr) | Yield | Materials $/kWh | Conversion $/kWh | Cell $/kWh (India / USA) |
|---|---|---|---|---|---|---|---|---|---|
| Salt-iron S03 | 1 | $5.9 M | 5,904 | 8 | 80 | 70 % | 573 | 1,894 / 2,936 | 2,790 / 3,915 |
| Salt-iron S03 | 10 | $29.6 M | 2,959 | 23 | 650 | 85 % | 446 | 753 / 995 | 1,314 / 1,575 |
| Salt-iron S03 | 100 | $148 M | 1,483 | 64 | 5,000 | 90 % | 318 | 350 / 414 | 721 / 790 |
| Salt-iron S03 | 1,000 | $743 M | 743 | 179 | 35,000 | 94 % | 191 | 167 / 184 | **380 / 398** |
| NFPP Na-ion N02 (comparison) | 1,000 | $80 M | 80 | 179 | 25,000 | 94 % | 56 | 23 / 40 | **83 / 102** |

Floor area (salt-iron, ×1.5 for the ceramic operations): 348, 539, 1,497 and 6,300 m² at 1, 10, 100 and 1,000 MWh/yr; NFPP: 232 to 4,200 m² [ASSUMPTION].

**Environmental controls**
- HCl scrubbers on melt synthesis and filling.
- Ni dust extraction (S01/S02 only).
- Dry rooms.
- Ceramic kiln emissions.
- Waste: off-spec cells are discharged before recycling (Na returns into NaCl); metals recovered as steel/Ni scrap; chloride residues neutralised.

**Working capital** at 1 GWh: ~60 days of materials plus 30 days of finished goods, about $61 M for salt-iron versus $16 M for NFPP (S15, India).

**Verdict at scale:** the salt-iron line is about 4–5× the cost of an NFPP Na-ion line, because of ceramic materials and ceramic-process capex. See `10_ECONOMICS` for the breakthrough conditions.
