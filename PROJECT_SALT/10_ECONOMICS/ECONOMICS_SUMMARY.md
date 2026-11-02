# Economics summary (brief §1.1, §11)

**Models:**
- `sim/s12_chemistry_matrix` — cell materials cost per architecture;
- `sim/s13_founder_targets/targets.py` — $3 interpretations and LCOS;
- `sim/s15_factory/factory.py` — scale scenarios and sensitivity.

Prices are wide [ASSUMPTION] ranges (`sim/s12_chemistry_matrix/prices.py`); only the BNEF benchmarks and the Altech capex are sourced.

## 1. The founder's $3, kept visible

| Interpretation | Salt-iron S03 | ZEBRA S01 | Na–Cl₂ S04 | NFPP Na-ion N02 | LFP benchmark | Plausible? |
|---|---|---|---|---|---|---|
| Theoretical minimum, reactants at feedstock price | **$0.26/kWh** | $6.42 | **$0.03** | $3.21 | $9.18 | below $3 only for salt+iron, Na–Cl₂, Fe-air ($0.37), RT Na-S ($1.67) |
| 1. $3/kWh cell (materials + conversion, 1 GWh floor) | floor $125 | $152 | $65 | $58 | $41 | **No** (13–50× gap) |
| 2. $3/kWh pack | floor ≥ $133 | ≥ $160 | ≥ $73 | ≥ $66 | ≥ $49 | **No** |
| 3. $3/kg of cells (= $/kWh at P50 Wh/kg) | = $22.9/kWh vs floor $125 | = $23.0 vs $152 | = $15.9 vs $65 | = $20.7 vs $58 | = $15.4 vs $41 | **No** for all; near (within 2×) only for Zn-ion and Fe-air |
| 4. $3 per finished unit | ≤ 24 Wh units | ≤ 20 Wh | ≤ 46 Wh | ≤ 52 Wh | ≤ 74 Wh | **Yes, for single small cells only** |
| 5. $3/kWh conversion cost (excl. materials) | floor $25+ | $25+ | $8+ | $8+ | $8+ | **No** |
| 6a. $3 per kWh delivered over life | LCOS $0.34–0.65 | $0.15–0.24 | $0.77–1.11 | $0.05–0.07 | $0.04–0.05 | trivially met (meaningless) |
| 6b. 3 ¢ per kWh delivered | no | no | no | near | near | only long-life LFP/NFPP |

The **theoretical minimum** is what the salt costs. Every practical cost is dominated by things that are not salt: ceramic, foils, separator, electrolyte, housings, capex and labour.

## 2. Cost per kWh by scale (S15, India / USA)
- **Salt-iron S03:** $2,790 / $3,915 (1 MWh/yr) → $1,314 / $1,575 (10) → $721 / $790 (100) → **$380 / $398 (1 GWh)**.
- **NFPP N02:** $809 / $1,934 → $326 / $586 → $165 / $234 → **$83 / $102**.
- **Benchmarks** [PUBLISHED PS-017]: lowest LFP cell $36/kWh (2025); average LFP pack $81/kWh; stationary packs $70/kWh.

## 3. Sensitivity (S03 cell materials P50 $192/kWh)
| Driver | Low → high | Materials $/kWh |
|---|---|---|
| β''-alumina price | $15 → $200/kg | 52 → 416 |
| areal capacity | 150 → 30 mAh/cm² | 90 → 374 |
| disc thickness | 0.5 → 1.5 mm | 125 → 333 |
| metal excess, NaAlCl₄ amount, packaging | – | < ±3 each |

**G4 case** (0.5 mm, 100 mAh/cm², $15/kg): **$31.5/kWh** materials. Conversion must also fall about 7× below the Altech anchor for the cell to approach LFP prices.

## 4. Laboratory and R0 costs
- R0 campaign parts and materials: about ₹12.5 lakh [ASSUMPTION; `06_PROCUREMENT/master_bom.csv`]. Partner-lab time is quote-only.
- Cost per lab cell: about ₹78,000 in parts (₹12.5 lakh ÷ 16 sub-assemblies) [CALCULATED]. Each cell holds about 0.6 Wh, so the lab cost is about ₹13 crore/kWh. This is meaningless for product cost and is shown only so nobody quotes the wrong number.

## 5. Lifetime cost
LCOS uses a simple annuity model (`targets.py: lcos`): system capex = 1.6 × pack, 330 cycles/yr, 90 % DoD, 90 % RTE, 1.5 % O&M, 8 % over 15 years. Molten-salt chemistries also lose 7–10 % of throughput to self-heating [PUBLISHED PS-011 basis].

## 6. Recycling credit
- **Salt-iron:** Fe and steel only (low value), so ~0.
- **ZEBRA:** Ni recovered through stainless-steel melting (historical route) is a real credit, ~$5–10/kWh at Ni $15/kg [ASSUMPTION].
- The S15 scrap model assumes 30 % value recovery of scrapped materials.
