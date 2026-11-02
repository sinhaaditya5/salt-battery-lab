# S10: Market sizing (India, bottom-up)
**Question:** What is the annual market for telecom-site and data-centre UPS backup batteries in India? How much of it does an "allowed indoors" product address?
**Inputs:**
- DoT tower count [LIT].
- JLL data-centre capacity [LIT].
- UPS runtime [LIT/ASSUMPTION].
- kWh per site, replacement interval, price band and shares [ASSUMPTION].
- Monte Carlo, 5,000 samples.
**Results** (`out/s10_results.json`):
- TAM ~$341M/yr [C-126].
- SAM ~$74M/yr [C-127].
- SOM ~$3.5M/yr after 5 years [C-128].
- Cross-check: paid-report UPS-battery market of $305–401M [C-029].
**Limits:**
- Low-confidence secondary sources.
- No primary customer data, which experiment K4 provides.
Run: `python run_s10.py`
