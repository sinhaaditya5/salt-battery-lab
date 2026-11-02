# S9: Techno-economics
**Question:**
- What does an R1 block cost bottom-up?
- How do installed cost and LCOS compare with LFP (including indoor fire protection and floor space) and VRLA?
- What would have to be true for R1 to win?
**Model:**
- Bottom-up materials from design masses × cited or assumed prices.
- Yield, labour, energy, overhead, and capex depreciation.
- 15-year UPS cost per kWh of 15-minute backup, including replacements, floor and fire protection.
- Telecom daily-cycling LCOS.
- Tornado, break-even map, learning curve.
**Refusal logic** (kept from the kit's cost model): a missing input stops the run, and every assumption must carry a range.
**Results** (`out/s09_results.json`):
- Cost $350/kWh [C-122].
- UPS 15-year cost R1 $1,228 / LFP $720 / VRLA $990 [C-123].
- Telecom LCOS R1 $0.42 / LFP $0.25 / VRLA $0.57 per kWh [C-124].
- Break-even needs a Li-ion fire-protection cost of ~$570/kWh at base.
**Limits:** No supplier quotes. Every price is an assumption or comes from low-confidence listings.
Run: `python run_s09.py`
