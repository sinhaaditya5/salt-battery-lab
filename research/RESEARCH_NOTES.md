# Research Notes: Aqueous Sodium-Ion for Indoor UPS / Commercial Storage (India first)

Compiled 2026-11-02. Every statement cites rows in `sources.csv`. Tags: VENDOR = company claim, LIT = independent / official / primary source, CALC = our arithmetic. Most rows rated "low" confidence come from search-result snippets; I could not open the full page for them. Treat them as leads to check, not as facts.

---

## 0. Ten decision-relevant findings

1. **Building codes do not treat an aqueous Na-ion battery as safe by default. Today they treat it as stricter than Li-ion.** The IFC 2024 permit table (Table 1207.1.3) sets lead-acid at 70 kWh, Li-ion at 20 kWh and Zn-MnO2 at 70 kWh. Anything unlisted counts as "Other battery technologies", with a threshold of **3 kWh** [SRC-079, SRC-080, SRC-081, SRC-082]. To be "allowed indoors", the company would need to get its own row in the table (Zn-MnO2 is the precedent [SRC-082, SRC-084]) or convince each local fire authority (AHJ) using UL 9540A data.
2. **NFPA 855-2026 changes the game.** The maximum-stored-energy table has been removed. A Hazard Mitigation Analysis (HMA) is now required by default. Testing means UL 9540A plus large-scale fire tests [SRC-085, SRC-086, SRC-087]. Explosion control is now NFPA 69 only. The edition explicitly exempts **lead-acid and aqueous nickel** systems, but not aqueous sodium. An aqueous Na-ion cell would have to show its hydrogen-evolution risk is handled, both by test and in the HMA [SRC-088, SRC-089]. Getting into a future exemption list is a concrete standards goal to pursue.
3. **The core technical gate for UPS is power, not energy.** Aquion's aqueous Mn-oxide module delivered **18.6 Wh/kg** at module level. Its peak power was only about **0.45 C** (1.0 kW on a 2.2 kWh module), and it was rated on a 20-hour discharge [SRC-034, SRC-035, SRC-037, SRC-038]. A 5-minute UPS needs roughly 12 C, and a 15-minute UPS roughly 4 C (CALC). Aquion lost 49% of its embodied energy when charge and discharge current went from 2 A to 10 A [SRC-039]. Any prototype plan must target high-rate operation at ≥10 mg/cm² from day one.
4. **The best evidence that aqueous Na-ion can work at realistic loading uses a perchlorate electrolyte.** Wu et al. (Nat Commun 2024) report 90 Wh/kg (on total electrode active mass) and 13,000 cycles at 10 C in coin cells at about 10 mg/cm². Their pouch cells ran at about 20 and over 30 mg/cm² [SRC-052, SRC-054, SRC-055, SRC-056, SRC-057]. But the electrolyte is **17 m NaClO4** [SRC-053]. Several other high-performing systems also rely on concentrated NaClO4 (17–17.6 m where the concentration is stated) [SRC-058, SRC-062, SRC-068]. NaClO4 is an oxidizer, which undercuts an "indoor-safe" message. The work on perchlorate-free routes (NaCl, acetate, dilute NaOTf with an interphase, Na2SO4) all reports lower capacity or shorter cycling demonstrations [SRC-060, SRC-069, SRC-072, SRC-074].
5. **Cell-level Wh/kg for aqueous Na-ion at ≥10 mg/cm² is almost never reported.** I screened about 25 abstracts from 2023–2026. Only one gave an areal loading. Wh/kg figures are always based on active or electrode mass [SRC-078]. Published values range from 47.7 to 117 Wh/kg on that basis [SRC-058, SRC-060, SRC-062, SRC-063, SRC-065]. For comparison, the only commercial aqueous Na product reached 18.6 Wh/kg at module level [SRC-035].
6. **The "non-flammable, indoor, data-centre" pitch is already crowded with *non-aqueous* Na-ion players who have far more capital.**
   - Peak Energy: $108M Series B, over $1B in orders, an AI data-centre JDA with Energy Vault [SRC-001, SRC-006, SRC-007].
   - Alsym: 135 Wh/kg cells, says it needs no active cooling at 800 VDC, explicitly targets AI data centres and basements/rooftops [SRC-011, SRC-013, SRC-014].
   - CATL, Gotion and BYD: 162–261 Wh/kg, storage cells claimed at over 10,000–20,000 cycles [SRC-021, SRC-023, SRC-024, SRC-025].
   - Whether Alsym's Na-Series uses an aqueous electrolyte is **unverified** [SRC-013, SRC-019].
7. **Natron is the closest cautionary example.** It used Prussian blue on both electrodes, targeted data-centre backup, and shut down on 3 Sep 2025. This came despite an ARPA-E grant and a planned 14 GWh plant. The causes cited were low energy density, which drives up capex per GWh, and investor pressure [SRC-028, SRC-029, SRC-030, SRC-031]. Aquion failed earlier for a similar reason: capital burn during ramp-up while Li-ion prices fell [SRC-032, SRC-033].
8. **Price target: incumbents in India are cheap.** BNEF 2025 puts the average stationary Li-ion pack at $70/kWh, $84/kWh in China, and $108/kWh across all segments [SRC-104, SRC-105, SRC-107]. Indian VRLA units listed on GeM work out to roughly ₹7,100–7,600 per nominal kWh. Indian 48 V LFP telecom packs list at about ₹10,800–21,600/kWh [SRC-119, SRC-121]. The beachhead price to beat is VRLA-in-India, not LFP. Note that VRLA nameplate kWh overstates usable energy at UPS discharge rates (not quantified here).
9. **An India data-centre UPS battery market measured in GWh is small; the money is in safety-driven premiums.** JLL projects 1.6 GW of data-centre capacity in June 2026 rising to 6 GW by 2029 [SRC-124]. At about 5 minutes of runtime [SRC-142], that is roughly 0.13 GWh rising to about 0.5 GWh of UPS batteries (CALC) [SRC-144]. India's BESS tender pipeline, by contrast, is 260–281 GWh [SRC-128, SRC-129]. Paid market reports put India's UPS battery market at $300–400M [SRC-137, SRC-138]. The wedge is a niche. Its value comes from avoided fire-rated rooms: FRNSW requires 240-minute rooms for Li-ion data-centre battery rooms [SRC-093]. Suppression adds 4–7% to project cost per one vendor [SRC-122].
10. **Funding windows are closing or need action now.**
    - Breakthrough Energy Fellows Cohort 7 Innovator track closes **today** (2 Nov 2026) [SRC-162].
    - Activate 2027 closed on 30 Oct 2026 [SRC-161].
    - ENTICE 3.0 explicitly wants **non-lithium** storage: up to $100k TA plus discom pilots [SRC-148]. No deadline was found, and one listing marks it "Inactive" [SRC-149].
    - The India RDI Fund requires TRL 4+ and goes through fund managers. TDB paused fresh applications from 30 Sep 2026 [SRC-150].
    - US SBIR was reauthorized in April 2026 after a lapse [SRC-159].

---

## A. Competitors

**Non-aqueous Na-ion (well-capitalized, data-centre-adjacent)**
- **Peak Energy.**
  - Raised a $108M Series B led by GM Ventures in Oct 2026, after a $55M Series A [SRC-001, SRC-002].
  - Building a 4 GWh/yr factory in Sacramento for about $71M, with production in Q1 2027 [SRC-003].
  - Cells are currently made in China to Peak's specification; it is an integrator today [SRC-004].
  - Customers: Jupiter Power up to 4.75 GWh (2027–2030), Energy Vault 1.5 GWh plus an AI data-centre JDA; over $1B in orders [SRC-005, SRC-006, SRC-007].
  - Electrolyte and cathode are not disclosed. The passive-cooling and 20% LCOE claims are unverified [SRC-009].
- **Alsym.**
  - Na-Series: 135 Wh/kg and 250 Wh/L at cell level, over 10,000 cycles, 2C/4C, RTE over 95%, −40 to 60 °C [SRC-011, SRC-012].
  - Branded "NFPP+"; electrolyte not stated [SRC-013].
  - Website claims 15,000 cycles, 800 VDC without active cooling, and targets AI data centres. No UL certification is shown [SRC-014].
  - Commitments: ERITY 9 GWh (binding status not disclosed), 18 GWh total announced, ESS Tech 8.5 GWh as a *non-binding* LOI [SRC-015, SRC-016, SRC-017].
  - Series C was $78M in April 2024, co-led by Tata Limited and General Catalyst [SRC-018].
  - High-volume production planned for 2027 [SRC-020].
- **China.**
  - CATL Naxtra: about 175 Wh/kg [SRC-021, SRC-022].
  - Gotion Gnascent: 261 Wh/kg for the High-Energy version. The storage version claims over 20,000 cycles but gives no Wh/kg [SRC-023, SRC-024].
  - BYD: third-generation platform with over 10,000 cycles [SRC-025].
  - HiNa: 10 GWh supply deal with Volta [SRC-026].
  - CATL–HyperStrong: 60 GWh cooperation [SRC-027].

**Aqueous / water-based and zinc**
- **Aquion (historical, aqueous Na/Mn-oxide).**
  - Raised about $200M. Went bankrupt in 2017 and its assets sold for $9.2M [SRC-032].
  - Module specs: 18.6 Wh/kg, 23.3 Wh/L, peak 0.45 C, 3,000 cycles to 70% [SRC-034, SRC-035, SRC-036, SRC-037, SRC-038].
- **Natron (Prussian blue).** Shut down in Sep 2025 [SRC-028 to SRC-031].
- **Offgrid Energy Labs (India, zinc-bromide ZincGel).** $15M Series A; aqueous status not stated; no deployments reported [SRC-040].
- **Eos (zinc).** Line 2 in commercial production, ramping to about 2 GWh/yr [SRC-045, SRC-046].
- **Enerpoly (zinc-ion).** Target of 100 MWh/yr by end-2026; status unverified [SRC-047].
- **Salient.** Nothing found [SRC-051].

**India**
- KPIT/Trentar: 110 Wh/kg cells; plan for a 3 GWh plant [SRC-041, SRC-042].
- Reliance/Faradion: no confirmed Na-ion production [SRC-043].
- Indi Energy: IIT Roorkee spin-off making hard-carbon pouch cells for lead-acid replacement [SRC-044].
- **Incumbents are moving to Li-ion.**
  - Amara Raja: cell plant delayed to FY27; 5 GWh BESS gigafactory targeted for Q4 FY27 [SRC-048, SRC-049].
  - Exide: Bengaluru cell-plant trials planned for 2026 [SRC-050].

---

## B. Literature (2023–2026 aqueous Na-ion full cells)

| Paper | Cathode ∥ Anode | Electrolyte | Loading | Wh/kg (basis) | Cycling | SRC |
|---|---|---|---|---|---|---|
| Wu, Nat Commun 2024 | Na2MnFe(CN)6 (Ni/C) ∥ NaTi2(PO4)3 | 17 m NaClO4 + NaOH ("alkaline") | ~10 (coin), ~20 and >30 mg/cm² (pouch) | 90 (anode+cathode mass) | 13,000 cyc @10C 74.3% (coin); pouch 85%/1,000 @20 mg/cm² | 052–057 |
| Yang, ACS AMI 2025 | NaMnHCF ∥ VOx-LSG | 17 M NaClO4 + 0.33 M Na4Fe(CN)6 | ~1 mg electrodes | 47.7 (both electrodes) | 62%/800 @1 A/g | 058–059 |
| Fu, Chem Sci 2025/26 | Mn@Fe/H-PBA ∥ polyimide | 1 M NaCl | ~1 mg/cm² | 74.32 (electrode mass) | pouch 500 cyc, 0.06%/cyc | 060–061 |
| Liang, Nat Commun 2023 | Fe-sub Mn-PBA ∥ PTCDI | conc. NaClO4 + Na4Fe(CN)6 additive | n.s. | 94 (active, both) | 73.4%/15,000 | 062 |
| Nat Commun 2025 | Na-rich birnessite ∥ NaxH2-xTi2O5 | n.s. | n.s. | 117.1 (active, both) | "long" | 063 |
| Zhao, ACS Nano 2024 | P'3 birnessite ∥ NTP | n.s. | n.s. | n.s. | 90.5%/60,000 (cell type unclear) | 064 |
| ACS AMI 2025 | tunnel Na0.66(Mn,Fe,Ti,Sn)O2 ∥ NTP@C | n.s. | n.s. | 80 (active, both) | 84%/1,000 @1C | 065 |
| Adv Mater 2026 | NaMnO2 | "phosphate-bonded perchloric" | **10 mg/cm²** | 82.31 (electrode material) | >1,440 h | 066 |
| Nano-Micro Lett 2026 | Mn-HCF ∥ PTCDI | 17.6 m NaClO4 + Fe(OTf)3 | n.s. | n.s. | 80%/20,000 | 068 |
| Liu, Nano-Micro Lett 2024 | Na2MnFe(CN)6 ∥ NTP | **dilute 2 m NaOTf** + interphase | n.s. | n.s. | 94.9%/200 | 069 |
| JMCA 2023 | HE-PBA ∥ NTP@C | **1 M Na2SO4** | n.s. | n.s. | 87%/1,000 @1C | 074 |
| Nano Research 2022 (bipolar) | Na2MnFe(CN)6 ∥ NTP, 6 bipolar electrodes, 8 V | water-in-polymer gel | n.s. | 86 (electrode mass) | up to 4,000 | 076 |

(n.s. = not stated in the abstract)

What the table says:
- **Mn dissolution.** Mitigations reported are Fe substitution, Fe(CN)6⁴⁻ additives, in-situ defect healing and Ni/C coatings [SRC-052, SRC-062, SRC-068, SRC-060]. Only Wu 2024 shows it working at realistic loading.
- **Bipolar stacking.** The only aqueous Na bipolar demonstration found is from 2022 [SRC-076]. There appears to be a gap in 2023–2026 work.
- **Non-aqueous benchmark.** Hard-carbon / Prussian-white pouch cells reach about 120 Wh/kg on a full-cell basis [SRC-077].

---

## C. Standards & certification

**US model codes**
- IFC 2024 permit thresholds: lead-acid 70, Li-ion 20, "other" **3 kWh**, Zn-MnO2 / NaNiCl / Ni 70 kWh [SRC-079 to SRC-082].
- One IFC-based local guide (Clark County) adds: Li-ion groups of no more than 50 kWh, and 2-hour separation inside buildings [SRC-083].
- The "other battery technologies 10 kWh" figure appears only in a low-confidence snippet attributed to **NFPA 855-2026 Table 1.3** [SRC-090]. Sources disagree on whether NFPA 855-2026 is still threshold-driven at all [SRC-091].

**NFPA 855-2026**
- Stored-energy table removed; HMA required by default; UL 9540A plus large-scale fire testing; NFPA 69-only explosion control; CCR at no more than 10% LFL [SRC-085 to SRC-089].
- The "600 kWh dedicated room" claim is unverified [SRC-092].

**Other jurisdictions and insurers**
- FRNSW (effective 3 Jun 2026): 240-minute FRL rooms for **Li-ion** data-centre UPS batteries [SRC-093].
- FM DS 5-32/5-33: not verified [SRC-094].

**India**
- **CEA 2026 BESS rules**, in force 1 Apr 2027 [SRC-095, SRC-096, SRC-097].
  - Apply above 650 V.
  - Require two-fault tolerance, suppression in every container and a third-party fire audit.
  - Set spacing by chemistry, naming Li-ion, Ni-Cd and lead-acid only. That means no category exists for aqueous Na-ion.
- The 2025 draft proposed water-based suppression above 200 kWh [SRC-098].
- BIS IS 16805 is IEC 62619, which is lithium-specific [SRC-099]. IS 16046 covers portable Li cells [SRC-100].
- TEC GR/TX/LIB-001/01 covers 48 V Li-ion for telecom [SRC-101].
- **No Indian standard or TEC GR for aqueous Na-ion was found.**

**Cost and time:** UL 9540A runs roughly $8k–100k+ and 2–12 weeks per level (vendor estimate) [SRC-102]. The current edition is disputed [SRC-103].

---

## D. Prices

**Li-ion benchmarks**
- BNEF 2025: all-segment average $108/kWh; stationary $70/kWh; LFP $81/kWh; China $84/kWh [SRC-104 to SRC-107].
- Lowest observed LFP cell / pack: $36 / $50/kWh (snippet) [SRC-108].
- The $117/kWh turnkey BESS figure was **not verified** (page returned 403).

**Manganese**
- MOIL EMD: ₹1,80,000/MT ex-GST [SRC-109].
- SMM EMD (LMO grade): $2,236–2,533/t [SRC-110].
- Battery-grade MnSO4: $896–1,137/t across 2026 [SRC-111].
- EMM: RMB 18,300/t [SRC-112].
- All of these are low confidence.

**Other inputs**
- Na2SO4: $150–165/MT, detergent grade [SRC-113].
- NaOH flakes: $490/MT, with conflicting figures elsewhere [SRC-114].
- Conductive carbon: $8–15/kg (estimate), and as much as about $38–40/kg for a 1-kg Super P lot [SRC-115, SRC-116].

**India pack prices**
- 48 V LFP: ₹52,000–1,08,000 per unit, or ₹10.8k–21.6k/kWh [SRC-117 to SRC-119].
- 12 V 100 Ah VRLA: ₹8,500–9,100 on GeM, or ₹7.1k–7.6k per nominal kWh [SRC-120, SRC-121].

**Fire protection:** 4–7% of project cost. In-building data-centre BESS runs $1,650–2,200/kWh installed (vendor; treat with caution) [SRC-122].

**Not found:** BMS $/kWh, stainless-steel foil, separators, casings, activated carbon, insurance premium effects [SRC-123].

---

## E. Market sizing

**Data centres**
- JLL: 1.6 GW (Jun 2026) to 6 GW (2029) [SRC-124].
- Cushman & Wakefield: 1,789 MW (H1 2026, different scope) [SRC-125].

**BESS**
- India added 8.2 GWh in H1 2026 (Mercom) [SRC-126].
- Tenders: 28 GW in H1 2026 [SRC-127].
- Pipeline figures conflict: 260 GWh (IESA-CES, Jul 2026) [SRC-128] versus 281 GWh (source not identified; breakdown sums to 268) [SRC-129]. End-2025 figure was 224 GWh [SRC-130].
- VGF for 30 GWh (Rs 54 bn) was reported on **16 Jun 2025** [SRC-131]. The 2023 VGF covered 4 GWh [SRC-132].
- Requirement of 236 GWh by FY32 [SRC-133].

**Telecom**
- 816,763 towers as of Dec 2024 [SRC-134]; 518,854 5G BTS [SRC-135]; Indus Towers 256,074 towers (Q2 FY26) [SRC-136].
- **Battery kWh per tower and replacement cycles were not found.**

**UPS batteries**
- India UPS battery market $305–401M (2024–25) [SRC-137, SRC-138]. Data-centre UPS market $375M (2025) [SRC-139].
- Li-ion share estimates conflict:
  - Report Cube: about 46% of India data-centre battery revenue [SRC-140].
  - Astute: lead-acid holds over 54% of India UPS batteries [SRC-141].
  - Global: about 40% of data-centre backup installs, 55% in hyperscale [SRC-143].
- Typical runtime is about 5 minutes for colo/cloud and 1–2 minutes for hyperscale [SRC-142]. The brief's "5–15 min" was not confirmed.
- Implied India data-centre UPS battery stock: about 0.13 GWh rising to about 0.5 GWh (CALC) [SRC-144].

---

## F. Y Combinator

- W27 Requests for Startups:
  - "Robots Made in America" explicitly lists "battery packs, and the machines that make them" [SRC-145].
  - "Data Center Supply Chain" cites a 3-year lead time for transformers and sold-out switchgear [SRC-146].
  - No RFS item is about energy storage itself.
- YC's Energy Storage industry page lists 11 companies. None makes aqueous or sodium cells [SRC-147].

---

## Open questions (not verified; do not treat as facts)

1. Is Alsym's Na-Series electrolyte aqueous? [SRC-013, SRC-019]
2. Is Peak Energy's electrolyte aqueous, and what is its cathode? [SRC-009]
3. What is the exact NFPA 855-2026 Table 1.3 row for "other" technologies? Does a sodium-ion or aqueous-sodium row exist? [SRC-090, SRC-091]
4. Do the FRNSW position and FM DS 5-32/5-33 apply to non-lithium chemistries? [SRC-093, SRC-094]
5. Does CEA Chapter XA apply to UPS batteries at or below 650 V? Will the CEA standards list name a non-lithium test standard? [SRC-096, SRC-097]
6. What is the cell-level Wh/kg and C-rate capability of any aqueous Na-ion pouch cell at ≥20 mg/cm² *without* perchlorate? (Nothing found.)
7. What is the source of the 281 GWh figure, and how does it relate to 260 GWh? [SRC-128, SRC-129]
8. Was any VGF decision taken on 14 May 2026? (Only the June 2025 approval was found [SRC-131].)
9. What is battery kWh per telecom tower in India, what is the VRLA vs Li-ion share in telecom, and how long are replacement cycles?
10. BMS $/kWh, current-collector foil, separator and casing prices; how much a fire-rated room costs per m²; the insurance premium differential between Li-ion and non-Li.
11. What is the ENTICE 3.0 deadline, and is the call still open? [SRC-148, SRC-149]
12. Can BNEF's turnkey BESS $117/kWh figure be confirmed from an accessible source?
