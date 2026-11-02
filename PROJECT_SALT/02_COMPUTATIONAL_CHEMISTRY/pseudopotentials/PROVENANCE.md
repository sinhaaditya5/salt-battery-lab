# Pseudopotential provenance

- **Family:** GBRV ultrasoft, PBE, v1.x (Garrity, Bennett, Rabe, Vanderbilt, *Comput. Mater. Sci.* 81, 446 (2014)).
- **Archive:** `tools/pseudo/gbrv_pbe_v1.5.tar.gz`, sha256 `4ebfeaa4c9d916c1ac2da6e89ec888fdffce096714f1956db01fea5ec9c9e4f0`. Downloaded in an earlier session; the URL is recorded in `sim/s06_dft_ec2/README.md`.
- **Files used in S11:**

| file | sha256 |
|---|---|
| na_pbe_v1.5.uspp.F.UPF | f84820c4280d21603bd50ae76a08e15c26864391ea055cf50affc4aedefc8f87 |
| cl_pbe_v1.4.uspp.F.UPF | 5b1ebdea1e5ba743fba0100806206287e1f7f00460c7e6f19791446beaee0655 |
| fe_pbe_v1.5.uspp.F.UPF | 6c132e6e7ac1c42df5cb6a13d0c99bb7af5bf3d6e2349f5658f0c22abfe3911a |
| co_pbe_v1.2.uspp.F.UPF | a5f392a0d35fc78cc9e2ac1636bb1cd02e9b80a063ea368e85be83b0e4523c45 |
| ni_pbe_v1.4.uspp.F.UPF | f76b86ce60cde3d83dfcc8df79ba05478db573d158289f1b226919442d977d25 |

- **Valence:** Na includes 2s2p semicore (9 e⁻); Fe/Co/Ni include 3s3p semicore.
- **Recommended cutoffs:** GBRV recommends 40 Ry / 200 Ry. We use 50 Ry / 400 Ry, chosen from our own convergence test.
