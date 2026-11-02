# Startup decision memo: Salt Battery

**To:** the founder · **From:** technical co-founder / analyst (Claude) · **Date:** 2 Nov 2026
**Basis:**
- this lab's 10 simulations and 164 logged sources (`research/sources.csv`);
- the claims ledger (`CLAIMS_LEDGER.csv`); claim IDs appear in brackets.

No cell has been built, so nothing below is measured.

---

## Verdict

### NO-GO on starting a water-based sodium battery *manufacturing* company on today's evidence.
### GO-WITH-CONDITIONS on a 12-week falsification sprint (≤ ₹10 lakh). Start with the near-free market test. Run discovery for the alternative wedge, battery fire-code / hazard-analysis software, alongside it, because it is the better company on today's evidence.

Why "no" for the factory company:

1. **Energy density sets the cost, and the cost is uncompetitive.**
   - Our bottom-up 12 V block stores **17.6 Wh/kg** (13.7–22.1) [CALC; C-115]. That is where Aquion's last module sat (18.6 Wh/kg [CALC; C-013]) before it went bankrupt after ~$200M [LIT; C-015].
   - The same materials cost **~$350/kWh** to make [CALC; C-122]. The best aqueous variant reaches about $150/kWh [CALC; C-125]. LFP packs sell at **$70/kWh** [LIT; C-005].
2. **The indoor premium doesn't close the gap at base assumptions.** The 15-year cost per kWh of 15-minute UPS backup is **R1 $1,228 / LFP $720 / VRLA $990** [CALC; C-123]. That LFP figure already includes fire protection. R1 wins only if all of these hold together:
   - an optimistic chemistry,
   - ≥15-year life,
   - lithium room and fire costs of ≥$150–250/kWh.
3. **Codes don't grant the advantage; they withhold it.** An unlisted chemistry gets **3 kWh** under IFC 2024, against lithium's 20 kWh [LIT; C-007, C-008]. NFPA 855-2026 requires a hazard analysis and large-scale fire testing for everyone, and exempts lead-acid and aqueous nickel from explosion control, but not aqueous sodium [LIT; C-010, C-011].
4. **The "non-flammable sodium" story is already being sold at far higher energy.**
   - Peak Energy has a $108M Series B and >$1B in orders [VENDOR; C-017, C-018].
   - Alsym claims 135 Wh/kg "NFPP+" [VENDOR; C-019].
   - Natron, with Prussian blue for data-centre backup, shut down in 2025 [LIT; C-016].
5. **India alone is a small prize** for this wedge: TAM ~$341M/yr, SAM ~$74M/yr, 5-year SOM ~$3.5M/yr [CALC; C-126…C-128].

Why not a flat "no": two assumptions could flip it, and both are cheap to test.
- (a) Some Indian buyers face a lithium-indoor premium or outright prohibition large enough (≥ $150–250/kWh).
- (b) A perchlorate-free cell reaches ≥30 Wh/kg block-level with ≥99.88% CE at 40 mg/cm².

## Proven vs simulated vs assumed

| Category | What we have |
|---|---|
| **Established in literature [LIT]** | R0 material and cell exist (83 mAh/g after 5,000 cycles at 2.8 mg/cm², electrode basis) [C-001, C-002]. Code thresholds and NFPA 855-2026 changes [C-007…C-011]. LFP prices [C-005]. Aquion and Natron outcomes [C-013…C-016]. |
| **Reproduced by us in software** | The kit's scripts reproduce its expected outputs 9/9 [C-101]. Nothing electrochemical has been reproduced. |
| **Simulated [SIM]** (screening, unvalidated) | 15-minute rate retention ~86% at 40 mg/cm² [C-104]. Rate collapses at 60 mg/cm² [C-105]. uMLIP voltage error MAE 0.33 V, with 0.7 V errors for NTP and Prussian white [C-110]. Birnessite interlayer 7.16 Å vs 7.19 Å XRD [C-111]. Thermal rise 2.8 K in a 15-min UPS discharge [C-119]. DFT+U LiFePO4 3.75 V vs 3.45 V literature [C-114]. |
| **Failed validation** | PyBaMM sodium DFN as shipped misses published curves by 67–121 mV against a 60 mV gate [C-102]. Voltages from our models carry ≥ ±0.1 V. |
| **Calculated [CALC]** | 17.6 Wh/kg block [C-115]. $350/kWh cost [C-122]. UPS TCO [C-123]. Telecom LCOS: R1 $0.42 vs LFP $0.25 vs VRLA $0.57 per kWh [C-124]. CE ≥ 99.88% needed for 3,000 cycles [C-107]. 1 M Na₂SO₄ crystallises below ~15–20 °C, so 0.5 M is used [C-027, C-204]. |
| **Assumed [ASSUMPTION]** | All material prices, process yields, capex, Li-ion fire-protection cost ($60/kWh base, $15–200 range) [C-201], VRLA life, market shares. |
| **Targets [TARGET]** | 3,000 cycles [C-202]; $150/kWh [C-203]; kill gates [C-206, C-207]. |

## The single riskiest assumption, and the cheapest experiment to test it

**Riskiest assumption:** *Indian telecom and data-centre buyers face a lithium-indoor cost or prohibition large enough (≥ $150–250/kWh of installed capacity) to pay 2–5 times lithium's cell cost for a water-based battery.*

Even a perfect cell can't fix this, so it comes before any lab work.

**Cheapest experiment (4 weeks, ~₹50k at most, no lab):**
- **Interviews:** 20 structured interviews with facility heads at tower companies, colocation operators, hospitals and mall/metro in-building telecom.
- **Quotes:**
  - two fire-protection or HMA quotes for an indoor Li-ion UPS room (≥100 kWh);
  - one quote from an Indian insurer.
- **Kill rule:** fewer than 3 of 20 name a lithium premium or prohibition of ≥ $150/kWh means stop the battery path [TARGET; C-207].

**Second experiment, only if the first passes:**
- **What:** reproduce the R0 powder (3 batches), then test 3, 20 and 40 mg/cm² electrodes in 0.5 M Na₂SO₄ with gas measurement.
- **Where:** a partner university lab under its safety approvals. The kit lists IIT Bombay and IIT Roorkee as leads; access is not agreed.
- **Cost and time:** about ₹4–8 lakh and 10–12 weeks (estimate, not quoted [C-205]).
- **Kill criteria:**
  - K1 capacity ≥ 60 mAh/g at 40 mg/cm² [C-206];
  - K2 CE ≥ 99.5%, heading to 99.88%;
  - K3 ≥ 60% at a 15-minute rate.

## First 90 days

| Weeks | Battery path (gated) | Software wedge (parallel, cheap) |
|---|---|---|
| 1–2 | Send lab-partner and author emails (`10_data_room/OUTREACH_PACK.md`). Book 20 buyer interviews. | Read NFPA 855-2026 and IFC 2024 primary text. Interview 5 fire-protection engineers or AHJs about HMA pain. |
| 3–4 | Interviews done, then the **K4 decision**. Collect fire-protection quotes. | Prototype an HMA/compliance report generator for one BESS archetype. Show it to 5 integrators. |
| 5–8 | If K4 passes, sign the lab scope and start powder synthesis. | If ≥2 integrators would pay, scope a paid pilot. |
| 9–12 | Electrode tests at 3/20/40 mg/cm² and gas measurement, then the **K1–K3, K5, K6 decisions**. | Decide which company to build. Update the YC interview story. |

## Skill gaps and whom to recruit

- **Founder gap:** no electrochemistry or cell-building track record, which the founder states openly. Hardware needs an **electrochemist co-founder** who has built aqueous or sodium-ion cells at ≥20 mg/cm². Without one, don't start the battery company.
- **Advisor needed either way:** a **fire-protection engineer** with NFPA 855 / UL 9540A / HMA practice. This person is the core co-founder candidate for the software wedge.
- **Later:** a manufacturing engineer (lead-acid or supercapacitor lines) and a power-electronics engineer (DC/DC, BMS). The concept PCB is a start.

## What would change this verdict to "go"

- **K4 passes:** ≥3 of 20 buyers with a ≥$150/kWh indoor-lithium premium or prohibition, plus quotes that confirm it.
- **The cell works:** K1–K3 pass in a perchlorate-free electrolyte at 40 mg/cm², with a measured CE trend towards ≥99.88%.
- **The cost path holds:** S9 re-run on measured capacity and two supplier quotes gives ≤ $250/kWh, with a path to $150.
- **An electrochemist co-founder commits.**

## EC2 / DFT status

- **Spend:** EC2 was used, with founder approval: c8g.8xlarge spot in Mumbai, $25 cap, 48 h hard stop. Spend at memo time was **under $1**.
- **Results so far:** see `sim/s05_atomistic/out/s05_summary.json`. They are screening only. The package is complete without them, and every headline number is [CALC] from the bottom-up model, not from DFT.
- **Cleanup:** terminate with `sim/s06_dft_ec2/terminate.sh`. Then **delete the root access key** in the AWS console.
