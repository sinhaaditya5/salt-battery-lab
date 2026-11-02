# Moonshot requirement calculator

`moonshot_requirements.py` performs arithmetic only. It converts vehicle energy consumption assumptions and a requested range/time into required usable energy and average terminal charging power. It also shows ideal active-cell mass for a user-entered Wh/kg assumption.

It does **not** simulate a chemistry, predict charging acceptance, include pack overheads or prove feasibility.

Example:

```powershell
py -3 simulation/moonshot_requirements.py --consumption-low 15 --consumption-high 20 --range-km 1500 --charge-minutes 5 --cell-whkg 875
```
