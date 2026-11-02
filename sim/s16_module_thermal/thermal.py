#!/usr/bin/env python3
"""S16 - thermal-management model of the SM-48T salt-iron module (engineering design D4).

Lumped model (one node for the hot box contents) - enough to size heaters and insulation, not to predict gradients:
  standby loss   Q = bridge * k * A_mean * (T_op - T_amb) / t          (flat-wall conduction, mean of inner/outer area)
  warm-up        m*cp*dT/dt = P_heater - Q(T), capped at the ramp limit; NaAlCl4 fusion absorbs latent heat at 157 C
  discharge      heat = heat_frac * P_out; does the module need its cooling bypass?
  cost           standby kWh/day and kWh/yr, and as a fraction of the module's stored energy
All inputs: params/smodule_params.py (THERMAL, MODULE, P1). Output: out/s16_results.json + s16_thermal.png/.svg.
Labels: results are [CALCULATED] from [ASSUMPTION] inputs; no thermal test exists.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; LAB = HERE.parents[1]; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
from params.smodule_params import MODULE as M, P1, THERMAL as T  # noqa: E402


def geometry():
    cols = int(round(M["stacks"] ** 0.5))                                   # 2 x 2 columns
    stack_h = M["series"] * (P1["thickness_mm"] + M["stack_pitch_mm"])
    inner = np.array([cols * P1["outer_mm"] + (cols - 1) * M["stack_gap_mm"] + 2 * 10.0,
                      cols * P1["outer_mm"] + (cols - 1) * M["stack_gap_mm"] + 2 * 10.0,
                      stack_h + 15.0])                                         # 10 mm side clearance, 15 mm busbar headroom
    t = M["insulation_mm"]
    outer = inner + 2 * (M["inner_wall_mm"] + t + M["outer_wall_mm"])
    area = lambda d: 2 * (d[0] * d[1] + d[0] * d[2] + d[1] * d[2]) / 1e6       # m2
    return dict(inner_mm=inner.round(1).tolist(), hotbox_outer_mm=outer.round(1).tolist(), stack_h_mm=round(stack_h, 1),
                A_inner_m2=area(inner), A_outer_m2=area(outer), A_mean_m2=(area(inner) * area(outer)) ** 0.5)


def standby_W(k, t_mm, A_mean, T_amb):
    return T["bridge_factor"] * k * A_mean * (T["T_op_C"] - T_amb) / (t_mm / 1000.0)


def masses(g):
    cell_g = (P1["granules_g"] + P1["NaAlCl4_g"]                               # cathode
              + (P1["plate_mm"] / 10) ** 2 * P1["plate_t_mm"] / 10 * 3.26      # beta'' plate
              + 2 * (P1["outer_mm"] / 10) ** 2 * P1["can_wall_mm"] / 10 * 8.4  # two sheet cans (Ni/SS avg)
              + 4 * (P1["plate_mm"] / 10) * (P1["frame_w_mm"] / 10) * (P1["frame_t_mm"] / 10) * 3.95)   # alpha frame
    cells_kg = M["cells"] * cell_g / 1000
    can_kg = g["A_inner_m2"] * M["inner_wall_mm"] / 1000 * 7900
    internals_kg = 6.0                                                         # busbars, heaters, spacers [ASSUMPTION]
    melt_kg = M["cells"] * P1["NaAlCl4_g"] / 1000
    return dict(cell_g=round(cell_g, 1), cells_kg=round(cells_kg, 2), can_kg=round(can_kg, 2), internals_kg=internals_kg,
                melt_kg=round(melt_kg, 2), C_J_K=cells_kg * 1000 * T["cp_cell_J_gK"] + (can_kg + internals_kg) * 1000 * T["cp_steel_J_gK"])


def warmup(C, P_heat, k, t_mm, A_mean, T_amb, melt_kg, dt=10.0):
    Tn, t, latent_left, ts, Ts = T_amb, 0.0, melt_kg * 1000 * T["melt_latent_J_g"], [0.0], [T_amb]
    ramp = T["ramp_C_min"] / 60.0
    while Tn < T["T_op_C"] - 0.05 and t < 48 * 3600:
        q_loss = standby_W(k, t_mm, A_mean, T_amb) * (Tn - T_amb) / (T["T_op_C"] - T_amb)
        net = P_heat - q_loss
        if net <= 0: return dict(reached=False, hours=None, t=ts, T=Ts)
        if abs(Tn - T["melt_T_C"]) < 0.5 and latent_left > 0:
            latent_left -= net * dt                                             # isothermal fusion plateau
        else:
            Tn = min(Tn + min(net / C, ramp) * dt, T["T_op_C"])                # controller enforces the ramp limit
            if Tn > T["melt_T_C"] - 0.5 and latent_left > 0 and Tn < T["melt_T_C"] + 0.5: Tn = T["melt_T_C"]
        t += dt; ts.append(t / 3600); Ts.append(Tn)
    return dict(reached=True, hours=round(t / 3600, 2), t=ts, T=Ts)


def main():
    g = geometry(); m = masses(g)
    res = dict(geometry=g, masses={k: v for k, v in m.items() if k != "C_J_K"}, heat_capacity_kJ_K=round(m["C_J_K"] / 1000, 1),
               module=dict(kWh=round(M["kWh"], 3), V_nom=M["V_nom"], Ah=round(M["Ah"], 2), P_max_kW=round(M["P_max_kW"], 3)))
    # 1) standby loss vs insulation
    ts = np.arange(10, 101, 5)
    sweep = {}
    for name, k in (("microporous board", T["k_microporous_W_mK"]), ("evacuated panel", T["k_vacuum_panel_W_mK"])):
        for Ta in T["T_amb_C"]:
            sweep[f"{name}, {Ta:.0f} C"] = [round(standby_W(k, t, g["A_mean_m2"], Ta), 2) for t in ts]
    res["standby_sweep"] = dict(t_mm=ts.tolist(), W=sweep)
    W_design = standby_W(T["k_vacuum_panel_W_mK"], M["insulation_mm"], g["A_mean_m2"], T["T_amb_C"][0])
    W_micro = standby_W(T["k_microporous_W_mK"], M["insulation_mm"], g["A_mean_m2"], T["T_amb_C"][0])
    day = lambda W: W * 24 / 1000
    res["standby_design"] = dict(
        insulation_mm=M["insulation_mm"], evacuated_W=round(W_design, 1), microporous_W=round(W_micro, 1),
        evacuated_kWh_day=round(day(W_design), 3), evacuated_frac_of_capacity_per_day=round(day(W_design) / M["kWh"], 3),
        microporous_kWh_day=round(day(W_micro), 3), microporous_frac_of_capacity_per_day=round(day(W_micro) / M["kWh"], 3),
        evacuated_kWh_yr=round(day(W_design) * 365, 1), evacuated_usd_yr=round(day(W_design) * 365 * T["grid_price_usd_kWh"], 2),
        self_sustain_hours_if_grid_lost=round(M["kWh"] * 1000 / W_design, 1),
        note="If the grid is lost and the module must keep itself hot, standby loss drains it; a cold (frozen) module needs hours to restart.")
    # 2) warm-up from cold at the design heater power
    wu = {}
    for P in (300.0, M["heater_W"], 1000.0):
        r = warmup(m["C_J_K"], P, T["k_vacuum_panel_W_mK"], M["insulation_mm"], g["A_mean_m2"], T["T_amb_C"][0], m["melt_kg"])
        wu[f"{P:.0f} W"] = dict(hours=r["hours"], reached=r["reached"]); wu[f"{P:.0f} W"]["_curve"] = (r["t"][::30], r["T"][::30])
    res["warmup"] = {k: {kk: vv for kk, vv in v.items() if kk != "_curve"} for k, v in wu.items()}
    ramp_floor_h = (T["T_op_C"] - T["T_amb_C"][0]) / T["ramp_C_min"] / 60
    res["warmup_ramp_limited_floor_h"] = round(ramp_floor_h, 2)
    # 3) discharge heat at max power vs standby loss
    P_out = M["P_max_kW"] * 1000
    q_dis = T["heat_frac_at_jmax"] * P_out
    dT_adiabatic = q_dis * (M["kWh"] / M["P_max_kW"]) * 3600 / m["C_J_K"]
    res["discharge"] = dict(P_out_W=round(P_out), heat_W=round(q_dis, 1), duration_h=round(M["kWh"] / M["P_max_kW"], 2),
                            standby_loss_W=round(W_design, 1), net_W=round(q_dis - W_design, 1),
                            adiabatic_rise_C=round(dT_adiabatic, 1),
                            cooling_bypass_needed=bool(dT_adiabatic > (OPER_MARGIN := 260.0 - T["T_op_C"])),
                            note=f"Heat at max rate exceeds standby loss, but the {T['T_op_C']:.0f}->260 C window ({OPER_MARGIN:.0f} K) absorbs a full discharge; "
                                 "the fan bypass is for abuse/over-temperature, not normal duty.")
    json.dump(res, open(OUT / "s16_results.json", "w"), indent=1)
    plot(res, wu, g)
    print(json.dumps({k: res[k] for k in ("geometry", "masses", "standby_design", "warmup", "warmup_ramp_limited_floor_h", "discharge")}, indent=1))


def plot(res, wu, g):
    import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply(); fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax = axs[0]; t = res["standby_sweep"]["t_mm"]
    styles = {"microporous board": ps.SERIES[1], "evacuated panel": ps.SERIES[0]}
    for lab, W in res["standby_sweep"]["W"].items():
        name, Ta = lab.rsplit(", ", 1)
        ax.plot(t, W, color=styles[name], ls="-" if Ta.startswith("25") else "--", lw=1.6, label=f"{name}, ambient {Ta}")
    ax.axvline(M["insulation_mm"], color=ps.MUTED, lw=0.8, ls=":"); ax.text(M["insulation_mm"] + 1, ax.get_ylim()[1] * 0.92, "design 40 mm", fontsize=7, color=ps.TEXT2)
    ax.set_yscale("log"); ax.set_xlabel("Insulation thickness (mm)"); ax.set_ylabel("Standby heat loss to hold 190 °C (W)")
    ax.set_title(f"Keep-warm power, SM-48T ({M['kWh']:.2f} kWh)"); ax.legend(fontsize=7)
    ax = axs[1]
    for i, (lab, v) in enumerate(wu.items()):
        tt, TT = v["_curve"]; ax.plot(tt, TT, color=ps.SERIES[i], lw=1.6, label=f"heater {lab}: {v['hours']} h" if v["hours"] else f"heater {lab}: not reached")
    ax.axhline(157, color=ps.MUTED, lw=0.8, ls=":"); ax.text(0.1, 159, "NaAlCl₄ melts (157 °C)", fontsize=7, color=ps.TEXT2)
    ax.set_xlabel("Time from cold start (h)"); ax.set_ylabel("Hot-box temperature (°C)")
    ax.set_title(f"Warm-up, ramp-limited to {T['ramp_C_min']:.0f} °C/min"); ax.legend(fontsize=7, loc="lower right")
    ps.save(fig, OUT / "s16_thermal", "SM-48T thermal model: standby loss versus insulation type and thickness, and warm-up from 25 C at three heater powers.",
            "[CALCULATED] lumped model from [ASSUMPTION] inputs (params/smodule_params.py); no thermal test")


if __name__ == "__main__":
    main()
