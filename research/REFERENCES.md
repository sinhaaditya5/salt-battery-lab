# External references (not redistributed)

During the study these documents were stored locally as PDFs, with text extractions. They are copyrighted by their publishers, so they are **not** committed. Download them from the sources below and place them at the listed paths to reproduce the local layout. No script in the repository requires them.

## Papers

| Local path | Citation | Link |
|---|---|---|
| `research/papers/Chayambuka2022_partII.pdf` | K. Chayambuka, G. Mulder, D. L. Danilov, P. H. L. Notten, "Physics-based modeling of sodium-ion batteries part II. Model and validation", *Electrochimica Acta* 404 (2022) 139764 | <https://doi.org/10.1016/j.electacta.2021.139764> |
| `research/papers/COMSOL_na_ion_battery_1d.pdf` | COMSOL Multiphysics 6.4 Application Gallery, "1D Isothermal Sodium-Ion Battery" (COMSOL Software License Agreement) | <https://www.comsol.com/models> (search "1D Isothermal Sodium-Ion Battery") |
| `work/shan2019.html` | X. Shan *et al.*, "Structural water and disordered structure promote aqueous sodium-ion energy storage in sodium-birnessite", *Nature Communications* 10 (2019) | <https://doi.org/10.1038/s41467-019-12939-3> |

The S2 validation (`sim/s02_pybamm_validation`) digitises one figure from Chayambuka *et al.* 2022, committed as `sim/s02_pybamm_validation/ref/fig4_p6_0_Im7.jpg`. It is the only part of these papers the code uses, and it remains © its authors and publisher.

## Datasheets (Texas Instruments)

These parts are used in the SCM-1 and BMS monitor boards (`pcb/`).

| Local path | Part | Link |
|---|---|---|
| `research/datasheets/ads131m08.pdf` | ADS131M08: 8-channel, simultaneous-sampling 24-bit ΔΣ ADC (SBAS950B) | <https://www.ti.com/product/ADS131M08> |
| `research/datasheets/amc3302.pdf` | AMC3302: ±50 mV reinforced isolated amplifier with integrated DC/DC | <https://www.ti.com/product/AMC3302> |
| `research/datasheets/amc3330.pdf` | AMC3330: ±1 V reinforced isolated amplifier with integrated DC/DC | <https://www.ti.com/product/AMC3330> |
| `research/datasheets/isow1044.pdf` | ISOW1044: isolated CAN FD transceiver with integrated DC/DC | <https://www.ti.com/product/ISOW1044> |
| `research/datasheets/lm5164.pdf` | LM5164: 100 V, 1 A synchronous buck converter | <https://www.ti.com/product/LM5164> |

## All other sources

Every other source, 164 for the aqueous track plus the Project Salt additions, is logged with URL, access date and claim IDs in [`sources.csv`](sources.csv) and [`sources_project_salt.csv`](sources_project_salt.csv).
