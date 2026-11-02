#!/usr/bin/env python3
"""One-RC equivalent-circuit + lumped thermal model for a measured R0 cell.

This is an engineering model, not an atomistic/electrochemical chemistry model.
All parameters must come from the team's measured data. The script refuses null
or missing parameters. Demo parameters supplied separately are synthetic only.

Current sign: positive = discharge; negative = charge.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path

REQ = ["capacity_Ah", "R0_ohm", "R1_ohm", "C1_F", "thermal_capacity_J_K",
       "thermal_conductance_W_K", "initial_soc", "initial_temperature_C", "ocv_curve"]


def load_params(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in REQ if d.get(k) is None]
    if missing:
        raise ValueError("Parameters must be measured and filled before simulation: " + ", ".join(missing))
    for k in REQ[:-1]:
        if not isinstance(d[k], (int, float)) or not math.isfinite(float(d[k])):
            raise ValueError(f"Parameter {k} must be a finite number")
    if d["capacity_Ah"] <= 0 or d["R0_ohm"] < 0 or d["R1_ohm"] <= 0 or d["C1_F"] <= 0:
        raise ValueError("Capacity and RC parameters must be physically positive; R0 may be zero")
    if d["thermal_capacity_J_K"] <= 0 or d["thermal_conductance_W_K"] < 0:
        raise ValueError("Thermal parameters are invalid")
    if not 0 <= d["initial_soc"] <= 1:
        raise ValueError("initial_soc must lie in [0,1]")
    curve = d["ocv_curve"]
    if not isinstance(curve, list) or len(curve) < 2:
        raise ValueError("ocv_curve must contain at least two [SOC, OCV_V] pairs")
    curve = sorted((float(x[0]), float(x[1])) for x in curve)
    if curve[0][0] < 0 or curve[-1][0] > 1:
        raise ValueError("OCV curve SOC values must lie in [0,1]")
    return d, curve


def ocv_at(soc, curve):
    soc = min(max(soc, curve[0][0]), curve[-1][0])
    for (s0, v0), (s1, v1) in zip(curve, curve[1:]):
        if s0 <= soc <= s1:
            if s1 == s0:
                return v1
            f = (soc - s0) / (s1 - s0)
            return v0 + f * (v1 - v0)
    return curve[-1][1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("parameters_json", type=Path)
    p.add_argument("current_profile_csv", type=Path, help="Columns: time_s,current_A,ambient_temperature_C")
    p.add_argument("--output", type=Path, default=Path("rc_simulation_output.csv"))
    args = p.parse_args()
    par, curve = load_params(args.parameters_json)
    with args.current_profile_csv.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("Current profile is empty")
    for needed in ("time_s", "current_A", "ambient_temperature_C"):
        if needed not in rows[0]:
            raise ValueError(f"Current profile missing {needed}")
    samples = []
    for n, r in enumerate(rows, start=2):
        try:
            samples.append((float(r["time_s"]), float(r["current_A"]), float(r["ambient_temperature_C"])))
        except Exception as e:
            raise ValueError(f"Invalid current-profile row {n}: {e}") from e
    if any(samples[i+1][0] <= samples[i][0] for i in range(len(samples)-1)):
        raise ValueError("time_s must be strictly increasing")

    soc = float(par["initial_soc"])
    temp = float(par["initial_temperature_C"])
    vp = 0.0  # polarization voltage across R1||C1
    tau = float(par["R1_ohm"]) * float(par["C1_F"])
    out = []
    for i, (t, current, ambient) in enumerate(samples):
        dt = 0.0 if i == 0 else t - samples[i-1][0]
        ocv = ocv_at(soc, curve)
        if dt > 0:
            # Positive current discharges the cell. Euler update of SOC and RC polarization.
            soc = min(1.0, max(0.0, soc - current * dt / (float(par["capacity_Ah"]) * 3600.0)))
            vp += dt * (current / float(par["C1_F"]) - vp / tau)
            heat_w = current * current * float(par["R0_ohm"]) + (vp * vp / float(par["R1_ohm"]))
            temp += dt * (heat_w - float(par["thermal_conductance_W_K"]) * (temp - ambient)) / float(par["thermal_capacity_J_K"])
            ocv = ocv_at(soc, curve)
        terminal_v = ocv - current * float(par["R0_ohm"]) - vp
        out.append({"time_s": t, "current_A": current, "soc_fraction": soc,
                    "ocv_V": ocv, "polarization_V": vp, "terminal_voltage_V": terminal_v,
                    "temperature_C": temp, "ambient_temperature_C": ambient,
                    "model_status": "PARAMETERIZED_MODEL_NOT_EXPERIMENTAL_RESULT"})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print(f"Wrote {args.output}; rows={len(out)}")
    print("This is an equivalent-circuit estimate. Validate against independent measured profiles before engineering decisions.")

if __name__ == "__main__":
    main()
