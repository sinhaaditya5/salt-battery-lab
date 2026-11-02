# S5: Atomistic screen with universal ML interatomic potentials
**Question:**
- Can universal MLIPs (MACE-MP-0b3, MACE-MP-0, CHGNet) reproduce known insertion voltages, migration barriers, and the birnessite interlayer spacing measured by XRD?
- What do they say about the R1 cathode?
**Structures** (`build_structures.py`):
- From Materials Project via OPTIMADE: LiFePO₄ mp-19017, LiMn₂O₄ mp-1272804, NaTi₂(PO₄)₃ mp-6761, Na₃Ti₂(PO₄)₃ mp-761046.
- Topotactic derivatives of those.
- A cubic Prussian-white prototype (MP has no entry).
- A 48-atom ordered birnessite model at 3 Na contents with 6 H₂O. The model is ordered; the real material is disordered.
**Methods:** FIRE relaxation with a cell filter. Climbing-image NEB, 7 images (`mlip_neb.py`).
**Validation set:** 5 voltages and 1 barrier with literature values (`literature_refs.json`).
**Key results** (`out/s05_summary.json`):
- MACE-MP-0b3 voltage MAE 0.33 V, max 0.71 V [C-110]. Errors are ~0.7 V for NTP and Prussian white, so uMLIPs are **not reliable** for those two.
- Birnessite interlayer 7.16 Å (CHGNet) vs 7.19 Å XRD [C-111].
- LiFePO₄ barrier 0.34 eV vs 0.27 eV GGA literature [C-112].
- Birnessite Na hop 0.39 eV [C-113].
**Label:** [SIM] uMLIP screen, not DFT-verified, except where S6 columns appear.
Run: `python build_structures.py; python mlip_relax.py mace_mp0b3; python mlip_relax.py chgnet; python mlip_relax.py mace_mp0; python mlip_neb.py mace_mp0b3; python analyze.py`
