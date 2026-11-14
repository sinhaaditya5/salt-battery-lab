## What and why

<!-- One or two sentences: what changes, and which claim, model or output it affects. -->

## Evidence checklist

- [ ] Every new or changed number carries a tag (`[LIT]`, `[VENDOR]`, `[CALC]`, `[SIM]`, `[ASSUMPTION]`, `[TARGET]`, …)
- [ ] New sources are logged in `research/sources*.csv`, and claims in `CLAIMS_LEDGER.csv`
- [ ] Nothing is tagged `[MEASURED]` unless it comes from a real, documented test
- [ ] Generated outputs were rebuilt by their script (no hand edits to `out/` folders)
- [ ] `make check` and `make test` pass locally, or CI is green
- [ ] No credentials, personal data or third-party copyrighted files are added

## Outputs affected

<!-- e.g. sim/s09_tea/out/*, DELIVERABLES/1_investor_docs/*, cad/out/* -->
