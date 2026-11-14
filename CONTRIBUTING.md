# Contributing

Thank you for taking the time to look at this lab. It is a single-founder research record, and outside review makes it better. Please read the [licence](LICENSE) first. The repository is public for review, but its contents are not licensed for reuse, so contributions are accepted as described below.

## The most useful contributions

1. **Claim corrections.** A number is wrong or outdated, a source has been superseded, or something is tagged `[LIT]` that should be `[VENDOR]`. Use the **Claim correction** issue template and link a primary source.
2. **Reproducibility bugs.** A script fails on a clean machine, an output differs from what is committed, or a test is flaky. Use the **Build or script bug** template.
3. **Model critique.** A physics or economics assumption that changes a conclusion. Open an issue first, so the change can be discussed before any code is written.

## Ground rules for changes

- **Every number carries a tag** (`[LIT]`, `[VENDOR]`, `[CALC]`, `[SIM]`, `[ASSUMPTION]`, `[TARGET]`, or the Project Salt equivalents) and resolves in `CLAIMS_LEDGER.csv`.
- **Nothing is `[MEASURED]`** until a real cell has been tested and the data are in the repository. `tests/test_params.py` enforces this.
- **Outputs come from scripts.** Never hand-edit files under `out/`, `DELIVERABLES/` or `PROJECT_SALT/`. Change the generator and re-run it.
- **Parameters live in one place.** Design values belong in `params/`, not in the scripts that consume them.
- **No credentials, personal data or third-party copyrighted files.** `scripts/check_repo.py` blocks the common cases.
- **DFT and cloud runs cost money.** Never add anything that launches AWS automatically.

## Development workflow

```bash
make setup          # venv + pinned CI requirements
make link           # expose the clone at the lab path the scripts expect
make check          # integrity gate
make test           # core test suites
make firmware-test  # SCM-1 firmware host tests
```

1. Fork the repository and create a branch: `fix/<short-name>` or `claim/<claim-id>`.
2. Make the change, re-run the affected generator, and commit the regenerated outputs in the same commit.
3. Write commit messages in [Conventional Commits](https://www.conventionalcommits.org/) style, for example `fix(s09): correct cathode price unit` or `docs(claims): update C-005 LFP pack price`.
4. Open a pull request and complete the evidence checklist in the template. CI must be green.

By submitting a contribution you agree that it may be incorporated into the repository under its existing licence terms. You also confirm that you have the right to submit it.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
