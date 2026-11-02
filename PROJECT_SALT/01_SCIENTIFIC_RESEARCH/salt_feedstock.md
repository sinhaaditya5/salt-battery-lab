# Common salt and seawater as battery feedstock (brief §2.1)

Numbers come from `sim/s13_founder_targets/targets.py` (part D) unless a source ID is given.

## 1. Which part of NaCl is useful, and where?

| Route | Chemistries | Na used? | Cl used? | NaCl per kWh of cell | Process energy per kWh of cell | Water | By-product | Label |
|---|---|---|---|---|---|---|---|---|
| **Direct**: NaCl is the discharged cathode | ZEBRA Na–NiCl₂ (S01/S02), salt-iron Na–FeCl₂ (S03) | Yes (Na⁺ shuttles through β''-alumina) | **Yes**: Cl⁻ stays in the cathode as MCl₂ ⇄ NaCl | 1.1–1.3 kg | ~0.2 kWh (drying and purification) | ~0.6 L | none from the salt | [CALCULATED]; purification energy [ASSUMPTION] |
| **Direct**: NaCl ⇄ Na + ½Cl₂ | Na–Cl₂ (S04) | Yes | **Yes**: Cl₂ is the cathode | 0.63 kg | ~0.1 kWh | ~0.3 L | none, but the cell holds Cl₂ | [CALCULATED] |
| **Soda ash (Solvay)** → Na₂CO₃ → cathode | All Na-ion (N01–N04, N07, N08) | Yes | **No**: Cl leaves as CaCl₂ effluent (~1 t per t soda ash) | ~1.6 kg | ~3.4 kWh | ~10 L | CaCl₂ brine, CO₂ | [CALCULATED] from [ASSUMPTION] Solvay inventory |
| **Natural soda ash (trona)** | Na-ion in the USA | Yes | n/a (no NaCl) | 0 | lower than Solvay [PUBLISHED PS-022] | – | – | [PUBLISHED] |
| **Downs cell** → Na metal | RT Na-S, Na-O₂, Na-metal anodes (N09, N11, N13) | Yes | **No**: Cl₂ co-product (1.54 kg per kg Na) must be sold | ~2.5 kg | ~9.8 kWh | 0 | Cl₂ | [CALCULATED]; ~10 kWh/kg Na [ASSUMPTION] |
| **Chlor-alkali** → NaOH | Na-ion precursors, aqueous electrolytes | Yes | **No**: Cl₂ co-product | – | ~2.0–2.5 MWh per t NaOH [PUBLISHED PS-023] | – | Cl₂, H₂ | [PUBLISHED] |

**Key finding.** Common salt is a *chemical* feedstock for every sodium battery. It is the *electroactive material*, with chloride doing work, only in the metal-chloride and Na–Cl₂ families. In Na-ion, "salt battery" is marketing; the chloride is waste.

## 2. Seawater

- Seawater holds about 35 g/L of dissolved salts, so about 29 L of seawater carries 1 kg of NaCl, plus the Mg, Ca and SO₄ that battery-grade salt must not contain [CALCULATED].
- India's solar salt pans (Gujarat, Tamil Nadu) already concentrate seawater using sunlight at near-zero energy cost. Evaporating it thermally would cost ~65 MJ per kg NaCl [CALCULATED from ASSUMPTION].
- **A battery company gains nothing by extracting its own sodium from seawater.** Buying industrial or vacuum salt, then drying and recrystallising it to battery grade, is cheaper by orders of magnitude. **Seawater is not free feedstock**; it is a solved upstream industry.

## 3. Purity a cell needs (salt-iron / ZEBRA route)

| Impurity | Why it matters | Working limit for R0 | Check | Label |
|---|---|---|---|---|
| H₂O | NaAlCl₄ hydrolyses to HCl and Al-oxychlorides; Fe/Ni passivate | < 100 ppm in granules | Karl Fischer (QT-06) | [ASSUMPTION] from ZEBRA practice |
| Ca, Mg | Exchange into β''-alumina (Ca²⁺ blocks Na⁺ paths) and raise resistance | < 50 ppm each | ICP-OES | [ASSUMPTION] |
| SO₄²⁻ | Reduces at the cathode and passivates it | < 100 ppm | ion chromatography | [ASSUMPTION] |
| K | Forms K-β''-alumina (higher resistance) | < 100 ppm | ICP-OES | [ASSUMPTION] |

Commercial reagent grades (≥99.9 %, low trace metals) meet these limits. Industrial solar salt does not without recrystallisation.

## 4. Supply: India and USA

- **USA:** ~40 Mt salt per year (2025); 42 % goes to the chemical industry [PUBLISHED PS-021]. Soda ash comes from trona (Wyoming); Searles Valley stopped soda-ash production in Feb 2026 [PUBLISHED PS-022]. Salt supply is not a constraint.
- **India:** a large solar-salt producer. Soda ash is made by the Solvay route from salt in Gujarat, so in India the Na in a Na-ion cell genuinely starts as sea salt. Production figures were not verified in this session [UNVERIFIED].
- **The real supply constraints are not the salt.** They are:
  - β''-alumina ceramic: very few suppliers worldwide. A sodium-beta-alumina ceramics programme exists at ARCI Hyderabad, but its document could not be retrieved [UNVERIFIED PS-031].
  - Ni powder (S01/S02).
  - Anhydrous AlCl₃ handling.

## 5. Is chloride safe?

Chloride in the cell is not automatically benign:
- **NaAlCl₄/AlCl₃ + water → HCl.** Cell breach in humid air releases HCl. The S-cell safety case must cover it.
- **Overcharge in Na-MCl₂** consumes NaAlCl₄ (2NaAlCl₄ + Ni → NiCl₂ + 2Na + 2AlCl₃ at ~3.05 V). AlCl₃ sublimes at ~180 °C.
- **Na–Cl₂** stores elemental chlorine with SOCl₂. This is why S04 fails the toxicity target despite its theoretical energy (1,825 Wh/kg [THEORETICAL]).
