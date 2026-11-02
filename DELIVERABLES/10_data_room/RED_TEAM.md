# Red team: two hostile readings of the package (2 Nov 2026)

Each attack names the claim it hits, says whether the claim survived, and gives the action taken.
Claim IDs refer to `CLAIMS_LEDGER.csv`.

## Critique 1: skeptical battery-industry investor (ex-Aquion / Natron board mindset)

| # | Attack | Verdict | Action |
|---|---|---|---|
| 1 | "Water-based sodium manganese is Aquion. Aquion raised ~$200M and sold its assets for $9.2M. What's different?" | **Partly survives.** We can change the market (indoor and priced safety, not off-grid $/kWh) and the design target (power first). We can't change the physics: our bottom-up block is 17.6 Wh/kg against Aquion's 18.6 (C-115, C-013). | The deck says "same energy class as Aquion" outright. The decision memo verdict is no-go as a factory company. |
| 2 | "Your $/kWh is a spreadsheet with no quotes." | **Survives as stated**, because every cost carries [ASSUMPTION] and the kit's refusal logic is kept. But the *headline* "~$350/kWh" could be read as a quote. | Labelled "cost, not price; assumed inputs; no supplier quotation" everywhere it appears (C-122). |
| 3 | "Non-flammable is not a moat. Peak and Alsym sell 'no thermal runaway' at 135+ Wh/kg." | **Survives.** | The competition slide puts non-aqueous sodium-ion first. "Non-flammable" was removed as a differentiator and kept only as a property. |
| 4 | "Your UPS case needs 4–12C. Aquion did 0.45C." | **Open.** S3 suggests ~86% at 4C at 40 mg/cm² (C-104), but S2 shows the model isn't validated for voltage (C-102). | K3 power gate added. S3 is labelled "not validated". |
| 5 | "Water electrolytes freeze, crystallise and gas. Who maintains it?" | **Survives, after a change.** 1 M Na₂SO₄ crystallises below ~15–20 °C, so we use 0.5 M (D-05). Gas and water budget needs CE ≥ 99.88% (C-107). Float duty is the worst case. | Operating range 5–45 °C [TARGET]. Gas and float gates are in the kill list. The float problem is stated on the safety slide. |
| 6 | "The best aqueous results use 17 m perchlorate. Is your 'safe' cell even possible?" | **Open.** No perchlorate-free full cell at ≥20 mg/cm² with cell-level Wh/kg was found in 2023–26 abstracts (SRC-078). | This is the core technical unknown, stated as such (C-026). |
| 7 | "Codes treat you worse than lithium today." | **Survives.** IFC 2024 'other' is 3 kWh (C-008). | This was the error in YC v1 (10 kWh); corrected in v2. Code listing appears as a multi-year cost on the roadmap. |
| 8 | "Indian lead-acid is ₹7k/kWh. Your 'indoor premium' customers don't exist in India." | **Untested; this is the riskiest assumption.** | It became experiment #1 (K4), run before any lab money is spent. |

## Critique 2: YC partner (founder–market fit, riskiest assumption)

| # | Attack | Verdict | Action |
|---|---|---|---|
| 1 | "Solo, non-electrochemist founder building a battery." | **Survives as a weakness**, stated honestly. | The application says it plainly and names the hire (electrochemist). The memo makes that co-founder a precondition for the factory path. |
| 2 | "What's the riskiest assumption? Not 'can we make the cell', but 'does anyone pay 3× lithium'." | **Agreed.** The original plan put the lab test first. | Reordered: the 4-week, near-zero-cost buyer test (K4) comes before the ₹4–8 lakh lab test. |
| 3 | "Why now?" | **Partly.** NFPA 855-2026 and India's lead-acid replacement wave are real "why now" signals (C-010, C-021). They help a *compliance* product more than a cell. | Alternative wedge B (fire-code / HMA software) moved up in "other ideas", with the YC W27 RFS fit (C-030). |
| 4 | "Is the market big enough?" | **No, for India-only cells:** SOM ~$3.5M/yr after 5 years (C-128). | Stated. Global indoor and telecom backup is the only venture-scale version, and there the incumbents are better funded. |
| 5 | "Do you understand your numbers?" | **Survives.** Every number traces to the ledger. Two v1 errors were found and fixed (IFC threshold; "lead-acid parity" insight withdrawn). | `DECISIONS.md`, `IDEA_v2.md` §5. |
| 6 | "Would we fund this?" | **Probably not as a cell company today. Possibly the founder**, given the rigour and willingness to kill the idea, applying with a sharper wedge. | YC answers v2 ask the founder to choose A or B before submitting. |

## Claims removed or reworded after the red team

- **Withdrawn:** "Indoors, the bar is lead-acid, so we only need lead-acid energy density." The bottom-up result is below lead-acid by volume and mass.
- **Corrected:** "Other battery technologies 10 kWh" is now 3 kWh (IFC 2024).
- **Removed:** "Win on installed cost including fire protection" as a *claim*. It's now a *hypothesis*, with break-even conditions (S9 map).
- **Reworded:** "Non-flammable battery" is now "the electrolyte can't burn". The PP case is the main fire load (C-121), and hydrogen remains a hazard.
- **Kept, now tagged:** all market numbers carry [CALC] with low confidence and cite the paid-report cross-check (C-029).
