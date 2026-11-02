"""S9 — Techno-economics: bottom-up R1 cost, installed cost vs LFP/VRLA incl. fire protection & floor,
LCOS for daily-cycling telecom duty, tornado, break-even map, learning curve.

Refusal logic kept from the kit's economics/cost_model.py: every input must exist in params COST/MAT
with a claim tag; ASSUMPTION inputs must carry a range. A missing input stops the run with a list.
Label: [CALC] from [LIT]/[ASSUMPTION]/[TARGET] inputs. Not a quote; no supplier quotation exists yet.
"""
import json, pathlib, sys, copy
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
import params.product_params as PP
from params.product_params import COST, MAT, P
import params.design as D

OUT = pathlib.Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)
REQUIRED = list(COST.keys())
UPS_LOADING, TELECOM_LOADING = 40.0, 80.0


def check_inputs():
    missing = [k for k in REQUIRED if k not in COST or COST[k] is None]
    bad = [k for k, v in COST.items() if isinstance(v, P) and v.tag == "ASSUMPTION" and v.rng is None]
    if missing or bad:
        raise SystemExit("TEA not run: missing inputs " + ", ".join(missing) + "; assumptions without range " + ", ".join(bad))


def vals(over=None):
    v = {k: (x.value if isinstance(x, P) else x) for k, x in COST.items()}
    v.update(over or {})
    return v


def s3_factor(loading, crate):
    r = json.loads((LAB / "sim/s03_r1_cell/out/s03_results.json").read_text())
    Ls = [float(x) for x in r["loadings_mg_cm2"]]
    key = lambda L: str(L) if str(L) in r["mc"] else repr(L)
    ret = [r["mc"][key(L)][str(float(crate))]["p50"] for L in Ls] if crate != 0.1 else [1.0] * len(Ls)
    vr = [r["nominal"][key(L)][str(float(crate))]["Vavg"] / r["nominal"][key(L)]["0.1"]["Vavg"] for L in Ls]
    return float(np.interp(loading, Ls, ret) * np.interp(loading, Ls, vr))


def monobloc_cost(v, loading, mat_over=None):
    mat = copy.deepcopy(MAT)
    for k, x in (mat_over or {}).items():
        mat[k] = P(x, mat[k].unit, mat[k].tag, mat[k].source, mat[k].rng)
    mb = D.monobloc(loading, mat); es = mb["electrode"]
    A = mb["repeats_per_cell"] * mb["plate_area_cm2"] * mb["n_cells"]          # cm2 of repeat units
    af = mat["active_fraction"].value; cf = mat["carbon_fraction"].value; bf = 1 - af - cf
    cath_kg = 2 * es["cathode_loading"] * A / 1e6; an_kg = 2 * es["anode_loading"] * A / 1e6
    carbon_kg = (cath_kg + an_kg) / af * cf; binder_kg = (cath_kg + an_kg) / af * bf
    steel_kg = 2 * mat["cc_thickness_um"].value * 1e-4 * mat["cc_density"].value * A / 1000
    sep_m2 = 2 * A / 1e4
    elyte_kg = es["electrolyte_mg_cm2"] * A / 1e6 + mb["free_electrolyte_kg"]
    na2so4_kg = elyte_kg / mat["electrolyte_density"].value * mat["electrolyte_molarity"].value * 0.142
    kWh = mb["energy_Wh"] / 1000
    mat_cost = {
        "cathode_active": cath_kg * (v["mn_precursor"] * 0.95 + v["naoh"] * 0.10 + v["cathode_processing"]),
        "anode_active": an_kg * v["ntp"], "carbon": carbon_kg * v["carbon_black"], "binder": binder_kg * v["binder"],
        "current_collectors": steel_kg * v["steel_foil"], "separator": sep_m2 * v["separator"],
        "electrolyte_salt": na2so4_kg * v["na2so4"], "case": mb["case_kg"] * v["case_pp"], "hardware": v["hardware"]}
    materials = sum(mat_cost.values()) / v["yield_"]
    energy = v["energy_kwh_per_kwh"] * kWh * v["electricity"]
    annual_kWh = v["plant_GWh"] * 1e6 * v["utilisation"]
    dep = v["capex_per_GWh"] * v["plant_GWh"] / v["depreciation_years"] / annual_kWh * kWh
    cash = materials + v["labour"] + energy
    total = cash * (1 + v["overhead_frac"]) + dep
    return {"kWh": kWh, "mass_kg": mb["mass_kg"], "materials_breakdown": mat_cost, "materials_after_yield": materials,
            "labour": v["labour"], "energy": energy, "depreciation": dep, "overhead": cash * v["overhead_frac"],
            "cost": total, "cost_per_kWh": total / kWh, "Wh_per_kg": mb["Wh_per_kg"], "Wh_per_L": mb["Wh_per_L"]}


def ups_tco(v, mat_over=None, loading=UPS_LOADING):
    """15-year cost per kWh of 15-minute backup energy (incl. replacements, floor, fire protection)."""
    m = monobloc_cost(v, loading, mat_over)
    f15 = s3_factor(loading, 4.0)
    cab = D.cabinet(loading)
    cab_cost = (m["cost"] * cab["monoblocs"] + v["cabinet_frame"]) / (1 - v["gross_margin"])
    cab_15 = cab["energy_kWh"] * f15
    r1_price_per_kWh15 = cab_cost / cab_15
    r1_floor = v["floor_cost"] * (0.6 * 0.8 * v["clearance_factor"]) / cab_15
    d, H = v["discount_rate"], v["horizon_years"]
    def repl(life, first):
        n = int(np.ceil(H / life)) - 1
        return first * sum((1 + d) ** (-(k * life)) for k in range(1, n + 1))
    r1 = r1_price_per_kWh15 + repl(v["r1_float_life_years"], r1_price_per_kWh15) + r1_floor
    lfp_first = v["lfp_ups_cabinet_installed"]          # Li-ion UPS cabinets deliver ~full energy at 15 min
    lfp = lfp_first + v["lfp_fire_protection"] + repl(v["lfp_life_years"], lfp_first) + v["floor_cost"] / v["lfp_footprint"]
    vrla_first = v["vrla_installed"] / v["vrla_15min_fraction"]
    vrla_life = PP.VRLA_REF["life_years"].value
    vrla = vrla_first + repl(vrla_life, vrla_first) + v["floor_cost"] / (v["vrla_footprint"] * v["vrla_15min_fraction"])
    return {"R1": r1, "LFP": lfp, "VRLA": vrla, "R1_price_per_kWh15": r1_price_per_kWh15, "R1_floor_per_kWh15": r1_floor,
            "R1_minus_LFP": r1 - lfp, "R1_minus_VRLA": r1 - vrla, "f15": f15, "cabinet_kWh15": cab_15}


def telecom_lcos(v, mat_over=None, loading=TELECOM_LOADING):
    """Levelised cost per kWh delivered, daily cycling at a weak-grid telecom site (48 V tray)."""
    m = monobloc_cost(v, loading, mat_over)
    mod = D.module48(loading)
    kW = 1.5
    tray_cost = (m["cost"] * PP.MODULE48["monoblocs"] + v["bms_per_module"] + v["dcdc_per_kW"] * kW + v["tray"]) / (1 - v["gross_margin"])
    kWh = mod["energy_Wh"] / 1000 * s3_factor(loading, 0.2)
    d, H, cyc = v["discount_rate"], v["horizon_years"], v["cycles_per_year_telecom"]
    def lcos(capex_per_kWh, cycle_life, cal_life, rte, dod=0.9):
        life = min(cycle_life / cyc, cal_life)
        n = int(np.ceil(H / life))
        pv_capex = sum(capex_per_kWh * (1 + d) ** (-(k * life)) for k in range(n) if k * life < H)
        pv_energy = sum(cyc * dod * (1 + d) ** (-y) for y in range(1, int(H) + 1))
        charge_cost = sum(cyc * dod / rte * v["electricity"] * (1 + d) ** (-y) for y in range(1, int(H) + 1))
        return (pv_capex + charge_cost) / pv_energy, life
    r1, r1_life = lcos(tray_cost / kWh, v["r1_cycle_life"], v["r1_float_life_years"], v["r1_rte"])
    lfp, lfp_life = lcos(v["lfp_pack"] * 3.0 + 60, v["lfp_cycle_life"], v["lfp_life_years"], v["lfp_rte"])   # telecom LFP sold ~3x pack + BMS/enclosure [ASSUMPTION]
    vrla, vrla_life = lcos(v["vrla_installed"], v["vrla_cycle_life"], PP.VRLA_REF["life_years"].value, v["vrla_rte"], dod=0.8)
    return {"R1": r1, "LFP": lfp, "VRLA": vrla, "R1_tray_price_per_kWh": tray_cost / kWh, "life_years": {"R1": r1_life, "LFP": lfp_life, "VRLA": vrla_life}}


def tornado(metric_fn, key_metric):
    base = metric_fn(vals())[key_metric]
    rows = []
    for k, x in COST.items():
        if isinstance(x, P) and x.rng is not None and x.tag in ("ASSUMPTION", "TARGET"):
            lo = metric_fn(vals({k: x.rng[0]}))[key_metric]; hi = metric_fn(vals({k: x.rng[1]}))[key_metric]
            rows.append({"input": k, "lo_value": x.rng[0], "hi_value": x.rng[1], "metric_at_lo": lo, "metric_at_hi": hi,
                         "swing": abs(hi - lo)})
    for k in ("cathode_capacity", "cathode_avg_potential_SHE", "anode_capacity", "active_fraction"):
        x = MAT[k]
        lo = metric_fn(vals(), {k: x.rng[0]})[key_metric]; hi = metric_fn(vals(), {k: x.rng[1]})[key_metric]
        rows.append({"input": "MAT." + k, "lo_value": x.rng[0], "hi_value": x.rng[1], "metric_at_lo": lo, "metric_at_hi": hi, "swing": abs(hi - lo)})
    rows.sort(key=lambda r: -r["swing"])
    return base, rows


def main():
    check_inputs()
    v = vals()
    res = {"label": "[CALC] from tagged inputs in params/product_params.py COST/MAT; not a quote",
           "monobloc_ups": monobloc_cost(v, UPS_LOADING), "monobloc_telecom": monobloc_cost(v, TELECOM_LOADING),
           "ups_tco_per_kWh15": ups_tco(v), "telecom_lcos": telecom_lcos(v)}
    b_mono, t_mono = tornado(lambda vv, mo=None: monobloc_cost(vv, UPS_LOADING, mo), "cost_per_kWh")
    b_ups, t_ups = tornado(lambda vv, mo=None: ups_tco(vv, mo), "R1_minus_LFP")
    b_tel, t_tel = tornado(lambda vv, mo=None: telecom_lcos(vv, mo), "R1")
    res["tornado"] = {"monobloc_cost_per_kWh": {"base": b_mono, "rows": t_mono[:12]},
                      "ups_R1_minus_LFP": {"base": b_ups, "rows": t_ups[:12]},
                      "telecom_R1_lcos": {"base": b_tel, "rows": t_tel[:12]}}
    # break-even map: R1 cabinet price multiplier vs Li-ion fire-protection cost
    fp = np.linspace(0, 250, 26); mult = np.linspace(0.5, 2.0, 31)
    grid = np.zeros((len(mult), len(fp)))
    for i, mu in enumerate(mult):
        for j, f in enumerate(fp):
            vv = vals({"lfp_fire_protection": f, "gross_margin": 1 - (1 - v["gross_margin"]) / mu})
            grid[i, j] = ups_tco(vv)["R1_minus_LFP"]
    res["breakeven"] = {"fire_protection": fp.tolist(), "price_multiplier": mult.tolist(), "R1_minus_LFP": grid.tolist()}
    # learning curve
    c_scale = res["monobloc_ups"]["cost_per_kWh"]
    Q = np.logspace(-2, 1, 40)            # cumulative GWh
    lr = v["learning_rate"]; b = np.log2(1 - lr)
    res["learning"] = {"cum_GWh": Q.tolist(), "cost_per_kWh": (c_scale * (Q / 0.5) ** b).tolist(), "anchor": "cost at 0.5 GWh cumulative = bottom-up scale cost"}
    (OUT / "s09_results.json").write_text(json.dumps(res, indent=1, default=float))
    charts(res)
    m = res["monobloc_ups"]; u = res["ups_tco_per_kWh15"]; t = res["telecom_lcos"]
    print(f"UPS monobloc: {m['kWh']*1000:.0f} Wh, cost ${m['cost']:.0f} -> ${m['cost_per_kWh']:.0f}/kWh (materials ${m['materials_after_yield']:.0f})")
    print(f"telecom monobloc: ${res['monobloc_telecom']['cost_per_kWh']:.0f}/kWh")
    print(f"UPS 15-yr cost per kWh of 15-min backup: R1 {u['R1']:.0f} | LFP {u['LFP']:.0f} | VRLA {u['VRLA']:.0f}  (R1 price {u['R1_price_per_kWh15']:.0f}, floor {u['R1_floor_per_kWh15']:.0f})")
    print(f"Telecom LCOS $/kWh: R1 {t['R1']:.3f} | LFP {t['LFP']:.3f} | VRLA {t['VRLA']:.3f}; lives {t['life_years']}")
    print("top UPS tornado:", [(r['input'], round(r['metric_at_lo']), round(r['metric_at_hi'])) for r in t_ups[:5]])


def charts(res):
    import plotstyle as ps
    import matplotlib.pyplot as plt
    # 1) monobloc cost waterfall-like stacked bar
    m = res["monobloc_ups"]
    parts = {**{k.replace("_", " "): v / m["kWh"] for k, v in m["materials_breakdown"].items()},
             "yield loss": (m["materials_after_yield"] - sum(m["materials_breakdown"].values())) / m["kWh"],
             "labour": m["labour"] / m["kWh"], "energy": m["energy"] / m["kWh"], "overhead": m["overhead"] / m["kWh"],
             "depreciation": m["depreciation"] / m["kWh"]}
    items = sorted(parts.items(), key=lambda kv: -kv[1])
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    cum = 0
    for i, (k, val) in enumerate(items):
        ax.barh(i, val, left=cum, color=ps.SERIES[0] if i < len(items) else ps.DEEMPH, height=0.55)
        ax.text(cum + val + 1, i, f"${val:.0f}", va="center", fontsize=7.5, color=ps.TEXT2)
        cum += val
    ax.barh(len(items), cum, color=ps.SERIES[1], height=0.55); ax.text(cum + 1, len(items), f"${cum:.0f}/kWh", va="center", fontsize=8, color=ps.TEXT)
    ax.set_yticks(range(len(items) + 1)); ax.set_yticklabels([k for k, _ in items] + ["total cost"])
    ax.invert_yaxis(); ax.set_xlabel("$ per nominal kWh (12 V monobloc, UPS design)")
    ax.set_title("R1 monobloc bottom-up cost (cost, not price)")
    ps.save(fig, OUT / "s09_cost_waterfall", "Bottom-up cost of one R1 12 V monobloc (UPS design, 40 mg/cm²) per nominal kWh at a 0.5 GWh/yr plant.",
            "[CALC] from [ASSUMPTION] material prices and process inputs (params COST); no supplier quotation")
    # 2) UPS TCO comparison
    u = res["ups_tco_per_kWh15"]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    names = ["VRLA", "LFP", "R1"]; valsx = [u["VRLA"], u["LFP"], u["R1"]]
    cols = [ps.ENTITY["VRLA"], ps.ENTITY["LFP"], ps.ENTITY["R1"]]
    ax.barh(names, valsx, color=cols, height=0.5)
    for i, val in enumerate(valsx):
        ax.text(val + 10, i, f"${val:,.0f}", va="center", fontsize=8, color=ps.TEXT2)
    ax.set_xlabel("15-year cost per kWh of 15-minute backup ($)")
    ax.set_title("Indoor UPS backup: total cost incl. replacements, floor, fire protection")
    ax.set_xlim(0, max(valsx) * 1.25)
    ps.save(fig, OUT / "s09_ups_tco", "15-year cost of providing 1 kWh of 15-minute UPS backup indoors: purchase, replacements, floor area and (for Li-ion) fire protection.",
            "[CALC] R1 from bottom-up cost + [TARGET] life; LFP/VRLA prices, lives, floor and fire-protection costs are [ASSUMPTION] ranges (params COST)")
    # 3) tornado for UPS advantage
    t = res["tornado"]["ups_R1_minus_LFP"]
    rows = t["rows"][:10][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    base = t["base"]
    for i, r in enumerate(rows):
        lo, hi = r["metric_at_lo"] - base, r["metric_at_hi"] - base
        ax.barh(i, lo, color=ps.SERIES[0], height=0.55); ax.barh(i, hi, color=ps.SERIES[1], height=0.55)
    ax.axvline(0, color=ps.TEXT2, lw=0.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["input"].replace("MAT.", "") for r in rows])
    ax.set_xlabel(f"Change in (R1 − LFP) 15-yr cost, $/kWh (base {base:+.0f})")
    ax.set_title("What moves the UPS business case")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=ps.SERIES[0]), plt.Rectangle((0, 0), 1, 1, color=ps.SERIES[1])],
              labels=["input at low end", "input at high end"], loc="lower right")
    ps.save(fig, OUT / "s09_tornado_ups", "Sensitivity of the R1-minus-LFP indoor UPS cost gap to each input swept across its range (negative = R1 cheaper).",
            "[CALC] one-at-a-time sensitivity over [ASSUMPTION]/[TARGET] ranges")
    # 4) break-even map
    b = res["breakeven"]
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    Z = np.array(b["R1_minus_LFP"])
    cs = ax.contourf(b["fire_protection"], b["price_multiplier"], Z, levels=np.linspace(-np.abs(Z).max(), np.abs(Z).max(), 21),
                     cmap=plt.matplotlib.colors.LinearSegmentedColormap.from_list("d", [ps.DIVERGING[0], ps.DIVERGING[1], ps.DIVERGING[2]]))
    ax.contour(b["fire_protection"], b["price_multiplier"], Z, levels=[0], colors=[ps.TEXT], linewidths=1.5)
    cb = fig.colorbar(cs, ax=ax, label="R1 − LFP 15-yr cost ($/kWh-15min)"); cb.outline.set_visible(False)
    ax.set_xlabel("Li-ion indoor fire-protection cost ($/kWh)"); ax.set_ylabel("R1 selling price vs base estimate (×)")
    ax.set_title("Where R1 beats Li-ion indoors (blue = R1 cheaper)"); ax.grid(False)
    ps.save(fig, OUT / "s09_breakeven_map", "Break-even between R1 and Li-ion for indoor UPS backup as a function of Li-ion fire-protection cost and R1 price; black line = parity.",
            "[CALC] from params COST ranges; fire-protection cost is the least-known input [ASSUMPTION]")
    # 5) learning curve
    L = res["learning"]
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    ax.plot(L["cum_GWh"], L["cost_per_kWh"], color=ps.SERIES[1], label="R1 monobloc cost (18 % learning rate)")
    ax.axhline(70, color=ps.ENTITY["LFP"], lw=1.5); ax.text(0.011, 74, "LFP stationary pack 2025: $70/kWh [LIT]", fontsize=7.5, color=ps.TEXT2)
    ax.set_xscale("log"); ax.set_xlabel("Cumulative production (GWh)"); ax.set_ylabel("$ per kWh")
    ax.set_title("Learning curve: R1 cost vs cumulative production"); ax.legend(loc="upper right")
    ps.save(fig, OUT / "s09_learning_curve", "R1 cost per kWh along an 18 % learning curve anchored at the bottom-up estimate for 0.5 GWh cumulative, vs the 2025 LFP stationary pack average.",
            "[CALC] learning rate [ASSUMPTION 12–22 %]; LFP price [LIT] BNEF 2025")


if __name__ == "__main__":
    main()
