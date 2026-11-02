# "BFT+U": not identified, so nothing was run under this name

The brief lists "BFT+U" and says the method must be identified before use and must not silently be replaced by DFT+U.

**What was checked (2 Nov 2026):**
- the founder's lab and tool folders;
- a filesystem search for "bft" (depth 4 from /, excluding system folders);
- installed Python packages and conda environments.

**Found:** nothing.

**Possible meanings, none confirmed:**
- a typo for DFT+U;
- DFT+U+V (extended Hubbard, available in QE 7.x as `HUBBARD` with `V` terms);
- "BdG" (Bogoliubov–de Gennes), which is not relevant to batteries.

**Action:** ask the founder. If DFT+U+V is meant, `sim/s11_dft_chlorides/campaign.py` can add inter-site V terms (Fe/Ni-3d – Cl-3p) in ~1 day of local compute.
