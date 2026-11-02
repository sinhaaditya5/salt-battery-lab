# Literature and industry landscape (brief §2, §13)

**Scope.** 30 architectures, in `chemistry_candidates.csv`, with balanced reactions in `balanced_reactions.md`.

**Sources.**
- `research/sources_project_salt.csv` (PS-001…PS-031, gathered 2 Nov 2026).
- `research/sources.csv` (SRC-001…SRC-164, earlier session, aqueous and competitor focus).

**Honesty notes.**
- Several items come from abstracts, university press releases or company announcements. They are labelled [PUBLISHED] only when the claim is the authors' own; company figures are [VENDOR CLAIM].
- Full texts were not read for PS-001, PS-004, PS-005 or PS-006.
- No patent claims were read in full.

## 1. Salt-literal chemistries (NaCl is the active material)

**ZEBRA Na–NiCl₂ (S01).**
- Molten Na | β''-alumina | NaAlCl₄ | Ni/NaCl at 270–350 °C. Cells are assembled discharged from NaCl + Ni [PUBLISHED PS-008/PS-009].
- Specific energy ~90–140 Wh/kg (cell), ~100–120 Wh/kg (battery). Cycle life 1,000–5,000 cycles, depending on source [PUBLISHED PS-010].
- Self-heating costs ~14 % of energy per day. A PNNL module measured 90 % battery efficiency and 80.9 % including heating [PUBLISHED PS-011].
- Commercial today through FZSoNick, e.g. 48TL telecom units with a 20-year technical life [VENDOR CLAIM PS-014].
- **UL 9540A large-scale fire-test data exist** (Battcon 2021 paper, not read). NFPA 855 threshold quantity: 20 kWh, or 70 kWh if listed to UL 1973 [PUBLISHED PS-015/PS-016]. That puts it on a par with lithium in the code tables — no regulatory advantage.

**Intermediate-temperature planar cells (S02/S03).**
- PNNL showed planar Na–NiCl₂ at 190 °C with 350 Wh/kg on a *material* basis over 1,000 cycles [PUBLISHED PS-006].
- PNNL also showed Na–FeCl₂ at 190 °C: 116 mAh/g at 33.3 mA/cm², and >295 Wh/kg (cathode basis) for 200 cycles [PUBLISHED PS-005].
- Assembling Fe + S-additive + NaCl in the discharged state is patented (Battelle US10615407B2, PS-007).
- **Companies:**
  - Inlyte Energy (US/UK; owns Beta Research; $8 M seed in 2023; Na–FeCl₂ grid storage) [VENDOR CLAIM PS-012].
  - Altech/Fraunhofer CERENERGY (DE; 60 kWh ABS60 prototype; >650 cycles with no fade claimed; €156 M for a 120 MWh/yr plant, i.e. ~€1,300 per kWh/yr of capacity) [VENDOR CLAIM PS-013, PS-032].

**Na–Cl₂ (S04).**
- Microporous carbon hosts Cl₂/NaCl in an AlCl₃–SOCl₂ electrolyte. ~3.5 V; 1,200 mAh/g on a *carbon* basis; ~200 cycles per the press release [PUBLISHED PS-001/PS-002].
- Theoretical energy is 1,825 Wh/kg for Na + ½Cl₂ → NaCl [THEORETICAL].
- The electrolyte and Cl₂ are acutely toxic. TRL ~3. Stanford holds the applications (PS-003).

## 2. Sodium-ion and sodium-metal systems

**Organic Na-ion (N01–N04).**
- Commercial: CATL Naxtra ~175 Wh/kg [VENDOR CLAIM]; Gotion up to 261 Wh/kg claimed [VENDOR CLAIM].
- Our build-up gives 145–177 Wh/kg P50 for NFPP, Prussian white and layered oxide, calibrated against CATL (+12 %).
- Peak Energy (US) raised $108 M (Series B, Oct 2026) and buys its cells from China [VENDOR CLAIM SRC-001].
- Natron (Prussian blue, data-centre power) shut down in 2025. Its patents sit with an assignment-for-benefit-of-creditors estate (PS-028).
- Faradion, owned by Reliance, holds the layered-oxide family in India (PS-029).

**Aqueous Na-ion (N05/N06).**
- Prior work: Shan et al. 2019 birnessite (SRC). The earlier S07 build-up gives 17.6 Wh/kg at block level; this matrix gives 19 Wh/kg at cell level, consistent.
- Aquion failed in 2017 at ~18.6 Wh/kg. Alsym positions itself as non-flammable at 135 Wh/kg "NFPP+" [VENDOR CLAIM SRC-019].

**Solid-state Na.**
- Quasi-solid NASICON (N07): reasonable chemistry, but its thin ceramic film is costly.
- Anode-free Na SSB (N08, Deysher et al., *Nat. Energy* 2024): Al-powder current collector; 400 cycles with NaCrO₂ at 99.96 % average CE. The 350 Wh/kg figure is a *theoretical* projection; measured cells have low energy density [PUBLISHED PS-004].

**Na–S.**
- High-temperature NAS (N10): mature, NGK/BASF. Molten Na + S has a documented fire history.
- Room-temperature Na–S (N09): best pouch evidence is 387 mAh/g-S after 937 cycles in a 10-layer pouch (Fraunhofer 2019) [PUBLISHED PS-025]. No verified practical Wh/kg.

**Na–O₂ (N11)** is TRL 2. Organic electrodes (N12) and FeS₂ conversion (N13) are TRL 3, with low practical energy.

## 3. Other abundant-element systems

| System | Status | Note |
|---|---|---|
| Zn-ion aqueous (A01) | TRL 6, several start-ups | Non-flammable; 54 Wh/kg P50; ranks above aqueous Na-ion for stationary use |
| Zn-air rechargeable (A02) | TRL 5 | Air-electrode durability |
| Fe-air (A03) | TRL 7 (Form Energy) | Multi-day storage only (C/100) |
| Al-ion chloroaluminate (A04) | TRL 3 | Electrolyte is a reactant, so ~41 Wh/kg |
| Al-air (A05) | Primary only | Mechanically "recharged" |
| Mg-ion, Ca-ion (A06/A07) | TRL 2–3 | Electrolyte chemistry unsolved |

## 4. High-energy benchmarks (physics references, not adopted)

| Benchmark | Our P50 cell Wh/kg | Calibration | Mechanism behind the energy |
|---|---|---|---|
| NMC811 / graphite-SiOx (21700) | 262 | +1 % vs ~260 | high-capacity Ni-rich CAM at 3.65 V |
| LFP / graphite | 195 | +7 % | cheap, long life, 3.2 V |
| NMC / Si-dominant anode | 380 | −13 % vs Amprius-class claims | removing the graphite mass |
| Li-metal SSB (anode-less) | 372 | +6 % vs developer claims | zero anode mass + ~3.7 V |
| Li-S lean electrolyte | 338 | −10 % | conversion cathode, light Li |

**Lesson for the founder.** Every cell at ≥360 Wh/kg combines a metal or alloy anode with very little excess, ≥3.6 V × ≥190 mAh/g intercalation (or Li-S conversion), and lean electrolyte. Sodium loses on two counts:
1. Its intercalation cathodes are ~25–35 % lower in Wh/kg-CAM (≈3.1–3.3 V × 120–165 mAh/g).
2. Its conversion partners (S, Cl₂, O₂) bring toxicity or cycle-life problems.

## 5. Fast charging in industry (claims, not verified)

- **CATL Shenxing gen-2 (Apr 2025):** 12C peak, >1.3 MW, "520 km in 5 min" CLTC [VENDOR CLAIM PS-018].
- **CATL Shenxing gen-3 (Apr 2026):** 10–80 % in 3 min 44 s and 10–98 % in 6 min 27 s. Same event: a Qilin "Condensed" variant claimed **1,500 km** for executive sedans [VENDOR CLAIM PS-020].
- **BYD (2025):** 1 MW at 1,000 V and 1,000 A, 10C [VENDOR CLAIM PS-019].
- **MCS connector:** 3,000 A × 1,250 V = 3.75 MW; deployed units deliver 1.0–1.2 MW [PUBLISHED PS-033].

These are lithium (LFP/NMC) systems. The founder's 1,500 km and fast-charge targets are being chased by lithium incumbents, not by any salt chemistry.

## 6. What remains unsolved (cross-family)

1. A sodium cathode above ~650 Wh/kg-CAM that keeps cycling.
2. A Na-metal plating CE ≥ 99.9 % at ≥ 10 mA/cm².
3. β''-alumina below ~$20/kg in thin (≤0.5 mm) large-area form.
4. A non-toxic electrolyte for Na–Cl₂.
5. Fast charging without plating (sodium or lithium) at ≥3 mAh/cm².
