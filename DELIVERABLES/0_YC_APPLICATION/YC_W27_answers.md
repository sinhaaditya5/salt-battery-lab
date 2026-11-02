# YC Winter 2027 application — copy-paste answers

**Version 1 · written 2 Nov 2026 (IST morning), before any simulation in this lab.**
**Deadline: Mon 2 Nov 2026, 8:00 pm PT = Tue 3 Nov 2026, 9:30 am IST** (confirmed on ycombinator.com/apply today).
Decision by 11 Dec for on-time applications. YC does **not** allow continuous editing after submission. Use the
update form (apply.ycombinator.com/app/edit) only for material changes, so **submit the strongest honest version once.**

How to use this file:
- Text inside `[[ FOUNDER: … ]]` is a field only you can fill (your history, dates, location). I have not invented any of it.
- The question wording follows YC's standard application; the live form sits behind login and
  may differ slightly. Match each answer to the closest question on the form.
- Answers are short on purpose. YC reads thousands of applications, and clarity beats length.
- The evidence for every number is in the table at the bottom (not for pasting).

---

## FOUNDERS

**Who writes code, or does other technical work on your product? Was any of it done by a non-founder?**

> I do all of it myself, with heavy use of AI coding tools (Claude Code). So far that work is a literature-reproduction kit for a published aqueous sodium-ion cell (Shan et al., Nature Communications 2019): synthesis work orders, a BOM, a cycler-data analyser, a cell-sizing calculator, an equivalent-circuit model, and a cost model that refuses to output numbers without real inputs. I'm now running open-source simulations (PyBaMM, machine-learned interatomic potentials, DFT+U) and concept CAD and PCB design. No non-founder has done technical work. No cell has been built yet. Wet-lab work will be done by a university battery lab under its safety approvals.

**Are you looking for a cofounder?**

> Yes. I'm looking for an electrochemist who has built and cycled aqueous or sodium-ion cells. They'd own cell design and testing. I'd own product, simulation, hardware, and customers.

**Founder video (1 minute):** see `YC_founder_video_script.md`. Only you can record it.

**Impressive thing you've built or achieved (per founder, one or two sentences):**

> [[ FOUNDER: one concrete, checkable achievement outside this startup: the hardest thing you have built, shipped, won or fixed. Give a number or outcome. Don't use this startup. ]]

**Time you most successfully hacked a non-computer system to your advantage:**

> [[ FOUNDER: a short true story. ]]

---

## COMPANY

**Company name:**

> [[ FOUNDER: name. Working name in this lab: "Salt Battery". ]]

**Describe what your company does in 50 characters or less.** (48 characters)

> Non-flammable sodium batteries for indoor backup

**Company URL / demo / product link:**

> None yet. [[ FOUNDER: optionally link the public data room once it exists. ]]

**What is your company going to make? Please describe your product and what it does or will do.**

> A water-based sodium-ion battery for places where lithium is hard to permit indoors: data-centre and telecom backup, hospitals, and basements of commercial and apartment buildings.
>
> The electrolyte is salt water (sodium sulfate) and the electrodes are manganese oxide and carbon. There's no flammable organic solvent, so there's no thermal-runaway fire. Lithium-ion batteries indoors increasingly need fire-rated rooms, spacing, suppression, and insurance sign-off. NFPA 855's 2026 edition tightened the indoor rules, and New South Wales now requires 240-minute fire-rated rooms for lithium in data centres.
>
> We won't beat lithium-iron-phosphate on cell price. BNEF's lowest LFP cell price is $36/kWh. We plan to win on installed cost once the fire-protection costs are included, and on cost per cycle. The first product is a 48 V backup module for telecom and UPS.
>
> Stage: pre-prototype. We have not built or tested a cell. Our first step is reproducing the published reference cell in a university lab, then testing it at commercial electrode thickness.

**Where do you live now, and where would the company be based after YC?**

> [[ FOUNDER: e.g. "<city>, India now. During YC: San Francisco. After: US parent company plus R&D and manufacturing in India." ]] Why: India has a large indoor-backup market (about 7.5 lakh telecom towers, data-centre capacity forecast to grow from 1.6 GW to 6 GW by 2029) and almost no domestic cell manufacturing. Cell R&D and labour are also cheaper there.

---

## PROGRESS

**How far along are you?**

> Pre-prototype. Done so far:
> (1) Picked a published, open-access reference cell (sodium-birnessite in aqueous Na2SO4) and turned it into a gated lab work package with a BOM, test matrix, and hazard register.
> (2) Found its weak points before spending lab money: electrode loading is ~2.8 mg/cm² versus 15–25 commercially, and the reported capacity counts electrode material only. The 2.5 V test window is about twice water's 1.23 V stability limit, so gas and manganese dissolution are expected.
> (3) Dropped every claim that was too big. Early on I was aiming for 5× lithium energy density and 1,500 km EV range, and I've abandoned both because the physics rules them out.
> (4) Now running open-source simulations (PyBaMM, ML-potential and DFT+U screens) and drawing up the concept module.
>
> Next: lab partner, then powder reproduction, then thick-electrode cells.

**How long have you been working on this? Full-time?**

> [[ FOUNDER: honest dates and hours. ]]

**What tech stack are you using, or planning to use? (Include AI models and AI coding tools.)**

> Cell work: university battery-lab cyclers, XRD, ICP and TGA, under the lab's safety approvals.
> Modelling: PyBaMM (electrochemistry), pymatgen/ASE with MACE-MP-0 and CHGNet ML potentials, Quantum ESPRESSO DFT+U on AWS, and Python techno-economic and Monte Carlo models.
> Hardware: build123d CAD to STEP, KiCad for the battery-monitor PCB, Blender for renders.
> AI: Claude Code (Anthropic) for nearly all code, analysis, and documents.

**Are people using your product?** No.

**Do you have revenue?** No.

**Previous YC application?** [[ FOUNDER: yes/no; if yes, what changed. ]]

**Incubator / accelerator participation?** [[ FOUNDER: none / details. ]]

---

## IDEA

**Why did you pick this idea to work on? Do you have domain expertise? How do you know people need what you're making?**

> I started out wanting a radically better battery and ran the numbers. 5× lithium energy density and 1,500 km EV range aren't reachable with sodium. A water-based cell also can't exceed about 1.23 V before it splits water. So I asked a different question: where is a heavy, low-voltage but non-flammable battery worth more than a light one?
>
> The answer is indoors. Lithium is now cheap ($70/kWh stationary packs, BNEF 2025), but indoor fire rules are tightening. NFPA 855's 2026 edition tightened indoor rules, and New South Wales mandates 240-minute fire-rated rooms for lithium in data centres. Lead-acid, the old "allowed indoors" answer, is still widely used in UPS and telecom backup. It lasts only a few years and contains lead.
>
> Domain expertise: [[ FOUNDER: be honest, e.g. "I'm not an electrochemist yet, which is why I'm recruiting one and starting with a published cell" ]].
>
> Evidence of need, which is still secondary: the code changes above; Alsym, a well-funded US startup, launching non-flammable sodium batteries aimed at data centres and basements in Oct 2025; and YC's own W27 request for data-centre supply-chain companies. I haven't yet interviewed customers. That is my next non-lab task, with 20 data-centre and telecom facility managers in India.

**Who are your competitors? What do you understand about your business that they don't?**

> - **Alsym Energy (US):** the closest. It sells non-flammable sodium-ion aimed at data centres, raised a $78M Series C, and is ahead of us.
> - **Lithium iron phosphate (CATL, BYD, and Indian assemblers):** the price leaders.
> - **Peak Energy:** non-aqueous sodium for outdoor grid storage, $108M Series B.
> - **CATL Naxtra:** about 175 Wh/kg sodium-ion.
> - **Lead-acid incumbents (Exide, Amara Raja):** they own the Indian UPS and telecom channels and are moving to lithium.
> - **The graveyard:** Aquion, a saltwater battery, went bankrupt in 2017 after ~$200M once lithium fell below its $300/kWh target. Natron, sodium Prussian blue, shut in 2025.
>
> What I think others miss:
> (1) Indoors, the bar is lead-acid, not lithium's 250 Wh/kg. An aqueous battery only needs lead-acid density with much longer life. Aquion failed by selling a ~17 Wh/kg system on $/kWh into off-grid and grid markets against falling lithium. We'll only sell where "allowed indoors" has a price.
> (2) Fire codes classify by chemistry. A new chemistry can start in the strictest bucket ("other battery technologies": 10 kWh in IFC-derived tables, versus 70 kWh for lead-acid) until large-scale fire-test data exists. So a UL 9540A dataset (no flame, no propagation, measured hydrogen) is part of the product, and we'll get it early.
> (3) In India, cells are mostly imported and Alsym isn't present. Water-based electrodes need no dry room, so a small, cheap pilot line is plausible there.

**How do or will you make money? How much could you make?**

> We sell battery modules and cabinets, priced per kWh against installed lithium plus its fire-protection costs, with a service contract for monitoring.
>
> Rough India-only size:
> - **Telecom backup:** ~7.5 lakh towers × ~5–10 kWh each, replaced every ~4–6 years ≈ 0.6–1.8 GWh/yr.
> - **Data-centre UPS:** capacity forecast to grow from 1.6 GW to 6 GW by 2029, at 5–15 minutes of backup ≈ 0.1–0.7 GWh/yr of new demand plus replacements.
>
> At ~$150–300/kWh that's roughly $100–700M a year in India. A 10% share would be about $10–70M a year in revenue. These are my estimates from public inputs, not a market study. The same product sells into indoor storage in the US, EU, and Australia, where fire codes are strictest.

**Which category best applies?**

> Hard tech / Climate & energy (choose the closest on the form).

**Other ideas you considered:**

> - A low-cost 8-channel battery cycler/potentiostat for university and startup battery labs. Testing equipment is a big capex barrier, and we'll build one anyway.
> - A fire-code compliance and installed-cost calculator for indoor battery projects. It's software we need for our own sales.
> - [[ FOUNDER: add any of your own. ]]

---

## EQUITY

**Have you formed any legal entity yet?** No. (YC's FAQ says incorporation isn't needed to apply.)
**Have you taken any investment?** [[ FOUNDER: No / details. ]]
**Are you currently fundraising?** [[ FOUNDER: e.g. "No. Exploring non-dilutive Indian grants for non-lithium storage." ]]

---

## CURIOUS

**What convinced you to apply? Did someone encourage you? YC events?** [[ FOUNDER ]]
**How did you hear about Y Combinator?** [[ FOUNDER ]]

---

## The riskiest assumption, the first experiment and the kill criterion
(Put this in the "How far along" box or in "Why this idea" if the form has room. Partners look for it.)

> **Riskiest assumption:** that a water-based sodium-manganese cell keeps its capacity and stays within safe gas limits at commercial electrode thickness. That means 15–25 mg/cm² instead of the paper's ~2.8 mg/cm², inside water's practical voltage window, over 1,000+ cycles.
>
> **First experiment:** at a partner university battery lab:
> - reproduce the published powder in three batches (XRD, ICP, TGA);
> - test it at ~3, ~10 and ~20 mg/cm² in three-electrode and sealed cells with gas measurement.
>
> It takes about 8–10 weeks. My estimate is a few lakh rupees (~$5–10k) in lab fees and materials, but it isn't quoted yet.
>
> **Kill criterion:** at ≥15 mg/cm², we stop this chemistry if any of these happens:
> - it loses more than half its thin-electrode capacity;
> - it fades more than 20% in 500 cycles;
> - it gasses faster than a lead-acid-style vent can handle.
>
> We then test the backup chemistry (Prussian-blue cathode with a NaTi2(PO4)3 anode) once. If both fail, we stop.

---

## Evidence behind each statement (do not paste; for your own defence in the interview)

| Statement | Tag | Source (checked 2 Nov 2026 unless noted) |
|---|---|---|
| Reference cell 83 mAh/g after 5,000 cycles at 1 A/g, electrode-material basis | [LIT] | Shan et al., Nat. Commun. 10, 4975 (2019), https://pmc.ncbi.nlm.nih.gov/articles/PMC6823464/ |
| Loading ~2.8 mg/cm² (5 mg on a 15 mm disc) | [CALC] | 5 mg / (π·0.75² cm²) = 2.83 mg/cm²; kit `01_R0_REFERENCE_CELL_SPEC.md` |
| Water stability window ~1.23 V | [LIT] | Standard thermodynamics; kit spec §6 |
| 5×, 1,500 km impossible | [CALC] | Kit `simulation/moonshot_requirements.py`; 1,500 km × 15–20 kWh/100 km = 225–300 kWh; 5 min → 2.7–3.6 MW |
| Stationary Li-ion pack avg $70/kWh; lowest LFP cell $36/kWh (2025) | [LIT] | BNEF via Energy-Storage.News / BNEF press release (re-checked 2 Nov 2026) |
| NFPA 855:2026 tightened indoor rules | [LIT] | https://www.energy-storage.news/nfpa-855-2026-edition-updates-and-what-they-mean-for-energy-storage-projects/ (thresholds conflict between secondary sources; quote primary text before the interview) |
| NSW 240-min rooms for Li-ion in data centres | [LIT] | https://www.energy-storage.news/fire-and-rescue-nsw-mandates-240-minute-fire-resistance-for-lithium-ion-battery-storage-rooms-in-data-centres/ |
| IFC-type threshold tables: lead-acid 70 kWh, Li-ion 20 kWh, "other battery technologies" 10 kWh | [LIT] | City permit worksheets citing IFC 2021 Table 1207.1.1 (Redmond WA, Mercer Island WA); CA Fire Code guide. 10 kWh value only seen in secondary sources; verify. |
| Alsym Na-Series launched Oct 2025, targets data centres, "non-flammable" | [VENDOR] | https://battery-tech.net/battery-markets-news/alsym-energy-debuts-na-series-sodium-ion-storage-batteries/ |
| Alsym $78M Series C (2024) | [LIT] | https://www.energy-storage.news/non-lithium-cobalt-free-ess-battery-startup-alsym-energy-tight-lipped-on-product-chemistry/ |
| Peak Energy $108M Series B (Oct 2026) | [LIT] | https://www.pv-magazine.com/2026/10/23/sodium-ion-storage-maker-peak-energy-raises-108-million-in-gm-led-round/ |
| CATL Naxtra ~175 Wh/kg | [VENDOR] | https://electrek.co/2026/04/22/catl-launching-sodium-ion-batteries-evs-2026/ |
| Aquion ~$200M raised, bankrupt March 2017, Li-ion fell below its $300/kWh target | [LIT] | MIT Technology Review, 8 Aug 2017 (re-checked) |
| Aquion module ~17 Wh/kg (26 kWh / 1,504 kg incl. rack) | [CALC] | Mission brief, original GTM article now redirects; re-verify from an archived datasheet before the interview |
| Natron shut down Sept 2025 | [LIT] | https://spectrum.ieee.org/natron-sodium-ion-battery-failure |
| India ~7.5 lakh telecom towers | [LIT] (secondary) | Exide-related market note via sahi.com; verify against TRAI/DoT |
| India data-centre capacity 1.6 GW (Jun 2026) → 6 GW by 2029 | [LIT] (secondary) | JLL via IANS, 2 Sep 2026: https://ianslive.in/indias-data-centre-capacity-expected-to-jump-to-6-gw-by-2029--20260902131252 |
| India added 8.2 GWh BESS in H1 2026 | [LIT] | https://www.ess-news.com/2026/09/14/india-adds-8-2-gwh-of-new-bess-capacity-in-h1-2026/ |
| YC W27 RFS "Data Center Supply Chain" | [LIT] | https://www.ycombinator.com/rfs |
| India market $100–700M/yr; 10% ≈ $10–70M/yr | [CALC]+[ASSUMPTION] | Kit-free arithmetic above; kWh/tower, replacement interval, minutes of backup and $/kWh are assumptions with ranges, to be replaced by S10 |
| Lab experiment ~8–10 weeks, ~$5–10k | [ASSUMPTION] | Founder estimate; no lab quote yet |

**Banned in this application** (and checked): "proven", "breakthrough", "zero risk", "cannot fail", "patented", "partnership", "LOI",
"EV-ready", any 5× or 1,500 km *target*. (They appear above only as abandoned goals, which is the honest story.)
