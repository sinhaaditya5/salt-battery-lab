# Security policy

## Reporting a vulnerability or exposed secret

**Do not open a public issue.** Report it privately instead, through [GitHub Security Advisories](https://github.com/sinhaaditya5/salt-battery-lab/security/advisories/new) for this repository.

Report anything that looks like:

- a credential, token or private key in any file or in the git history;
- personal data that should not be public;
- a script that could launch paid cloud resources without an explicit, per-run confirmation;
- a dependency or download that is fetched without integrity verification.

You should receive an acknowledgement within 72 hours. Credentials are revoked first and investigated second.

## Safeguards in this repository

- `scripts/check_repo.py` runs in CI on every push and pull request. It fails on AWS keys, private-key blocks, common API-token formats, credential-like filenames and oversized files.
- `.gitignore` excludes key files (`rootkey.csv`, `*.pem`, `.env*`) and cloud credential files.
- `tools/aws/aws_env.sh` loads AWS credentials into the current shell only, from a file outside the repository, and never prints them.
- Cloud scripts (`sim/s06_dft_ec2/launch.sh`, `tools/ec2_build/`) enforce spot pricing, a hard stop time and a dollar cap. `run_all.sh` never launches cloud machines.
- Third-party downloads (`scripts/fetch_assets.sh`) are pinned by SHA-256.

## Physical safety

This repository contains **concept designs only**. Nothing has been built or tested. The designs are not for fabrication, and they must not be used to build, charge or operate batteries. The R0 kit and the S-cell build manual assume a qualified laboratory with the hazard controls listed in their own documents.
