# YC Winter 2027 application — copy-paste answers (v2)

**v2 · 2 Nov 2026, ~12:00 IST · replaces v1 (kept as `YC_W27_answers_v1_superseded.md`).**
**Deadline: Mon 2 Nov 2026, 8:00 pm PT = Tue 3 Nov 2026, 9:30 am IST** (confirmed on ycombinator.com/apply).
YC does not allow editing after you submit (FAQ). Only material changes can go through apply.ycombinator.com/app/edit, so submit once, honestly.

## What changed since v1, and why (read this first)

1. **One v1 number was wrong.** IFC 2024 puts an unlisted chemistry such as aqueous sodium at **3 kWh**, not 10. Lead-acid gets 70 kWh and Li-ion 20 kWh. So today the code treats our battery *more strictly* than lithium until it is tested and listed. Zinc-MnO₂ earned its own 70 kWh row, which is the precedent we would follow. (research/sources.csv SRC-079…084)
2. **Our own model no longer supports "we win on installed cost".**
   - Making a water-based cell comes out at roughly **$150–350/kWh** in our model, against a $70/kWh LFP stationary pack (BNEF 2025) [CALC from assumed prices, no quotes yet; S9].
   - Indoors, it only beats lithium when two things hold together: the lithium room and fire costs exceed about $150–250/kWh, **and** our battery lasts about 15 years. v2 says this plainly and makes it the riskiest assumption.
3. **Non-aqueous sodium-ion firms already sell "no thermal runaway".** Alsym's "NFPP+" claims 135 Wh/kg [VENDOR], and Peak Energy has a $108M Series B and >$1B in orders [VENDOR]. Both are added to the competitor answer.
4. **New findings worth showing YC** (all are simulation or arithmetic, not lab results):
   - The paper's 1 M Na₂SO₄ electrolyte would crystallise below roughly 15–20 °C, so we moved to 0.5 M.
   - A sealed cell needs ≥99.88% coulombic efficiency to last 3,000 cycles before it loses 20% of its water.
   - The bottom-up energy density lands near Aquion's 18.6 Wh/kg module.
5. **Second idea promoted.** NFPA 855-2026 now requires a Hazard Mitigation Analysis for essentially every battery installation (SRC-086). That makes a software product for battery fire-code compliance and permitting a serious alternative. It is listed under "other ideas". **Decide which idea leads before you submit** (see the end of this file).

How to use: replace each `[[ FOUNDER: … ]]` with your own facts. The wording follows YC's standard form, so match each answer to the nearest box. The evidence table is at the bottom (don't paste it).

---

## FOUNDERS

**Who writes code, or does other technical work on your product? Was any of it done by a non-founder?**
> I do all of it, with heavy use of AI coding tools (Claude Code). So far that's:
> - A reproduction kit for a published water-based sodium-ion cell (Nat. Commun. 2019).
> - A lab of open-source models: PyBaMM electrochemistry, machine-learned and DFT+U atomistic screens on AWS, gas and thermal models, and a bottom-up cost model.
> - Concept CAD and a battery-monitor PCB.
>
> No non-founder has done technical work. No cell has been built. Wet-lab work will be done by a university battery lab under its safety approvals.

**Are you looking for a cofounder?**
> Yes. I'm looking for an electrochemist who has built and cycled aqueous or sodium-ion cells at real electrode loadings.

**Impressive thing you've built or achieved:** [[ FOUNDER ]]
**Hacked a non-computer system:** [[ FOUNDER ]]

---

## COMPANY

**50 characters or less** (46): `Water-based sodium batteries for indoor backup`

**What is your company going to make?**
> A water-based sodium-ion battery for places where lithium is hard to permit indoors: telecom sites, data-centre UPS rooms, hospitals and building basements.
>
> The electrolyte is salt water, so there is no flammable solvent and no thermal runaway. The product is a 12 V block in the same box size as the lead-acid blocks that UPS and telecom racks already use.
>
> What we've learned from our own models is that it won't win on cost per kWh. Lithium iron phosphate packs are $70/kWh, and our bottom-up estimate is 2–5 times that, because water-based cells store ~20–35 Wh/kg. It can only win where lithium's indoor costs are high, or where lithium isn't allowed at all, and only if it lasts ~15 years.
>
> Stage: pre-prototype, no cell built. The first step is a 10–12-week lab test of the two things that decide the company.

**Where do you live now, and where would the company be based after YC?** [[ FOUNDER ]]
> Suggested reason: India has ~7.5 lakh telecom towers still largely on lead-acid. Lead-acid costs ~₹7,100–7,600/kWh there and has to be replaced every few years. Cell R&D and labour are also cheaper.

---

## PROGRESS

**How far along are you?**
> Pre-prototype. In the last [[N]] weeks:
> (1) I turned a published water-based sodium cell into a gated lab work package.
> (2) I built an open simulation lab, and it changed the plan:
> - the paper's 1 M sodium sulfate would crystallise below ~15–20 °C, so we use 0.5 M;
> - a sealed cell needs ≥99.88% coulombic efficiency or it dries out before 3,000 cycles;
> - our cost model says we're 2–5 times lithium per kWh;
> - fire codes today treat an unlisted chemistry *more* strictly than lithium (3 kWh vs 20 kWh in IFC 2024).
>
> (3) I dropped my original EV and multi-fold-energy goals because the physics rules them out.
>
> Next: lab partner, then reproduce the material, then test thick electrodes.

**Tech stack (incl. AI models and AI coding tools)?**
> - Lab: cyclers, XRD, ICP and TGA at a university partner.
> - Models: PyBaMM; MACE-MP-0 and CHGNet ML potentials; Quantum ESPRESSO DFT+U on AWS spot; Python cost and Monte Carlo models.
> - Hardware: build123d CAD, KiCad, Blender.
> - AI: Claude Code for nearly all code and analysis.

**Are people using your product?** No.
**Do you have revenue?** No.
**Previous application / incubator?** [[ FOUNDER ]]

---

## IDEA

**Why did you pick this idea? Domain expertise? How do you know people need it?**
> I started out trying to build a radically better EV battery and killed that goal with arithmetic. Water-based cells can't beat lithium on energy. Their real advantage is that the electrolyte can't burn, and that only matters where fire risk is priced.
>
> The pricing is moving our way. NFPA 855's 2026 edition now requires a hazard analysis and large-scale fire testing for essentially every installation. New South Wales requires 240-minute fire-rated rooms for lithium UPS batteries in data centres. Indian telecom still runs largely on lead-acid that needs frequent replacement.
>
> Domain expertise: [[ FOUNDER: be honest — e.g. "I'm not an electrochemist; I'm recruiting one and starting from a published cell" ]].
>
> Need is not yet proven. I haven't interviewed customers. My next non-lab task is 20 interviews with Indian telecom and data-centre facility managers to measure the real cost of keeping lithium or lead-acid indoors.

**Who are your competitors? What do you understand that they don't?**
> - **Lithium iron phosphate:** $70/kWh packs; the default.
> - **Non-aqueous sodium-ion:**
>   - Peak Energy: $108M Series B, >$1B orders, an AI data-centre deal.
>   - Alsym: claims 135 Wh/kg and no thermal runaway, and targets data centres.
>   - CATL Naxtra: ~175 Wh/kg.
> - **Lead-acid incumbents:** Exide and Amara Raja, both moving to lithium.
> - **Zinc:** Eos; Offgrid Energy Labs in India.
> - **Graveyard:**
>   - Aquion (water-based sodium; 18.6 Wh/kg modules, 0.45C max power) went bankrupt in 2017 after ~$200M.
>   - Natron (Prussian blue, data-centre backup) shut in 2025.
>
> What I think others miss:
> 1. A water-based cell can't win on $/kWh. Aquion and Natron both died partly from low energy density, which meant more capital per GWh. So we'll only sell where non-flammability is priced, and we'll design for power (UPS needs 4–12C, Aquion managed 0.45C).
> 2. Codes reward *listed, tested* chemistries, not "safe" ones. An unlisted chemistry starts at 3 kWh, stricter than lithium. Zinc-MnO₂ earned its own 70 kWh row. Large-scale fire-test data and a code listing are part of the product, and we'd start on them in year one.
> 3. The best published water-based sodium results use 17 m sodium perchlorate, an oxidiser. A perchlorate-free, crystallisation-safe electrolyte at real loading is the technical gap we'd test.

**How will you make money? How much?**
> We'd sell 12 V blocks and 48 V telecom trays per kWh, priced against lead-acid life-cycle cost and lithium plus indoor fire costs.
>
> India telecom backup is about ~7.5 lakh towers × 5–10 kWh, replaced every ~4–6 years, which is about 0.6–1.8 GWh a year (my estimate). Data-centre UPS in India is small in energy terms, at ~0.1–0.5 GWh/yr.
>
> At ~$200–300/kWh that's a $150–600M/yr addressable market in India, and a 5–10% share would be $10–60M/yr. These are estimates, not a market study.

**Category:** Hard tech / Climate & energy.

**Other ideas you considered:**
> 1. **Battery fire-code and permitting software.** NFPA 855-2026 now requires a Hazard Mitigation Analysis for essentially every battery installation and drops the fixed size thresholds. Every BESS and data-centre UPS project now needs code research, fire-test interpretation and AHJ back-and-forth. I built much of that analysis for my own product. This fits your "AI for City Hall" and "Data Center Supply Chain" requests.
> 2. A low-cost 8-channel battery cycler for university and startup labs, where test equipment is the capex barrier.

---

## EQUITY / CURIOUS
**Legal entity?** No (YC FAQ: not needed to apply). **Investment taken?** [[ FOUNDER ]] **Fundraising?** [[ FOUNDER ]]
**What convinced you to apply / how did you hear?** [[ FOUNDER ]]

---

## Riskiest assumption, first experiment, kill criteria (put in "How far along" or "Why this idea")
> **Riskiest assumption** (two parts, both must hold):
> (a) a perchlorate-free water-based sodium cell reaches ≥30 Wh/kg at block level, ≥99.9% coulombic efficiency and ≥80% capacity at a 15-minute discharge, at ≥40 mg/cm² electrodes;
> (b) Indian telecom and data-centre buyers pay ≥$150/kWh more to keep lithium indoors, or can't use it at all.
>
> **First experiment (10–12 weeks).**
> - At a partner university lab: reproduce the published powder (3 batches, XRD/ICP/TGA), then test 3, 20 and 40 mg/cm² electrodes in 0.5 M Na₂SO₄ with gas measurement.
> - In parallel: 20 buyer interviews and two quotes for lithium-room fire protection.
> - Cost: a few lakh rupees (~$5–10k) in lab fees and materials. This is my estimate, not yet quoted.
>
> **Kill:** at 40 mg/cm²
> - any of:
>   - capacity below 60 mAh/g;
>   - coulombic efficiency below 99.5%;
>   - less than 60% capacity at a 15-minute rate;
> - or fewer than 3 of 20 buyers name a lithium indoor premium of ≥$150/kWh.
>
> If any of these hits, I stop the battery and pursue the compliance software instead.

---

## DECIDE BEFORE SUBMITTING: which idea leads?
- **A. Keep the salt battery as the main idea** (this file). It's honest and shows rigour, but our own numbers show it's a hard, capital-heavy bet with well-funded competitors.
- **B. Lead with the battery fire-code / HMA software** and keep the battery as the "other idea". NFPA 855-2026 is a concrete "why now"; it's capital-light, the analysis is already built, and it matches two YC W27 requests. If you choose B, ask me (or rewrite) the Company/Idea answers. The facts are in `research/RESEARCH_NOTES.md` §C.
- Recommendation: see `DELIVERABLES/STARTUP_DECISION_MEMO.md` once written. Interim view: **B is the stronger YC application on today's evidence.** A is defensible only if you're determined to do hardware and can recruit an electrochemist.

---

## Evidence behind each statement (do not paste)

| Statement | Tag | Source |
|---|---|---|
| IFC 2024 thresholds: lead-acid 70, Li-ion 20, other 3, Zn-MnO₂ 70 kWh | [LIT] | research/sources.csv SRC-079…082 (Clark County NV IFC 2024 guide) |
| NFPA 855-2026: max-energy table removed; HMA by default; UL 9540A + large-scale fire test; lead-acid & aqueous-Ni exempt from explosion control | [LIT] | SRC-085…089 |
| NSW 240-min rooms for Li-ion DC UPS batteries | [LIT] (low conf.) | SRC-093 |
| LFP stationary pack $70/kWh (BNEF 2025) | [LIT] | SRC-104/105; energy-storage.news BNEF coverage |
| R1 cost $150–350/kWh; 2–5 times LFP | [CALC] | sim/s09_tea (assumed material prices, no quotes) |
| ~20–35 Wh/kg block energy | [CALC] | params/design.py; sim/s09_tea scenario grid |
| Aquion module 18.6 Wh/kg, 0.45C max | [CALC] from [VENDOR] datasheet | SRC-035, SRC-038 |
| 1 M Na₂SO₄ crystallises below ~15–20 °C | [CALC] from [LIT] solubility | params MAT (4.76 g/100 mL at 0 °C; 13.9–19.5 at 20 °C) |
| CE ≥ 99.88 % for 3,000 cycles before 20 % water loss | [CALC] | sim/s04_gas |
| Peak $108M, >$1B orders; Alsym 135 Wh/kg NFPP+ | [VENDOR] | SRC-001, 006, 007, 011, 013 |
| Natron shut 2025; Aquion bankrupt 2017 | [LIT] | SRC-028…033 |
| Best aqueous Na results use 17 m NaClO₄ | [LIT] | SRC-052, 053 (Wu, Nat Commun 2024) |
| India VRLA ₹7,100–7,600/kWh; 48 V LFP ₹10,800–21,600/kWh | [CALC] from listings | SRC-119, 121 (low confidence) |
| India DC 1.6 → 6 GW (JLL) | [LIT] (press) | SRC-124 |
| Telecom 0.6–1.8 GWh/yr; India TAM $150–600M | [CALC]+[ASSUMPTION] | to be replaced by S10 |
| Lab test ~$5–10k, 10–12 weeks | [ASSUMPTION] | no quote yet |

Banned-phrase check: no "proven", "breakthrough", "zero risk", "cannot fail", "patented", "partnership", "LOI", "EV-ready", and no multi-fold-energy or long-range EV targets.
