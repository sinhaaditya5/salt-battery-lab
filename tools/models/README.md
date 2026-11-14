# ML interatomic potential weights

`sim/s05_atomistic/mlip_relax.py` loads foundation-model weights from this folder. They are third-party files, 44 MB and 79 MB, so they are **not committed**. Fetch and verify them with:

```bash
scripts/fetch_assets.sh models
```

| File | Upstream | SHA-256 |
|---|---|---|
| `mace-mp-0-medium.model` | [ACEsuit/mace-mp](https://github.com/ACEsuit/mace-mp) release `mace_mp_0` (`2023-12-03-mace-128-L1_epoch-199.model`) | `01bfe221…0ed35845` |
| `mace-mp-0b3-medium.model` | [ACEsuit/mace-foundations](https://github.com/ACEsuit/mace-foundations) release `mace_mp_0b3` | `2f2be696…9826b012` |

CHGNet weights ship inside the `chgnet` Python package.
