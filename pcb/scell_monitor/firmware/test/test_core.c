/* Host unit tests for scm_core.c:  make -C pcb/scell_monitor/firmware test */
#include <stdio.h>
#include <string.h>
#include "../scm_core.h"

static int fails = 0, checks = 0;
#define CHECK(cond, msg) do { checks++; if (!(cond)) { fails++; printf("FAIL: %s (line %d)\n", msg, __LINE__); } } while (0)

static SCM_Inputs nominal(uint32_t t, int32_t T) {
    SCM_Inputs in; memset(&in, 0, sizeof in);
    in.t_ms = t; in.n_cells = 1; in.cell_mv[0] = 2300; in.data_fresh = true;
    for (int k = 0; k < 4; k++) in.tc_dc[k] = T;
    return in;
}

/* run the core through heat-up with a thermal plant that follows the setpoint (first order) */
static SCM_Outputs run_to_ready(SCM_Core *c, uint32_t *t, int32_t *T) {
    SCM_Outputs o = {0};
    for (int i = 0; i < 25; i++) { SCM_Inputs in = nominal(*t, *T); in.cmd_start = (i > 20); o = scm_step(c, &in); *t += 100; }
    for (int i = 0; i < 2000000 && c->state != ST_READY && c->state != ST_FAULT; i++) {
        SCM_Inputs in = nominal(*t, *T); o = scm_step(c, &in); *t += 100;
        if (*T < o.setpoint_dc) *T += 1;        /* plant tracks setpoint (<= 0.1 C per tick, faster than ramp) */
    }
    return o;
}

int main(void) {
    SCM_Core c; uint32_t t = 0; int32_t T = 250; SCM_Outputs o;
    /* 1 boot -> selftest -> heatup -> ready */
    scm_init(&c); o = run_to_ready(&c, &t, &T);
    CHECK(c.state == ST_READY, "reaches READY at set point");
    CHECK(o.interlock_closed, "interlock closed only in READY");
    CHECK(T >= SCM_T_SET_DC - 50, "temperature near set point");
    CHECK(t / 60000 >= (SCM_T_SET_DC - 250) / SCM_RAMP_DC_PER_MIN - 1, "heat-up respects ramp limit (>= (Tset-25)/ramp minutes)");
    /* 2 over-voltage trip latches and opens interlock */
    SCM_Inputs in = nominal(t, T); in.cell_mv[0] = SCM_V_TRIP_HIGH_MV + 1; o = scm_step(&c, &in); t += 100;
    CHECK(c.state == ST_FAULT && (c.fault_flags & F_V_HIGH), "V_HIGH -> FAULT");
    CHECK(!o.heat_en && !o.interlock_closed && o.buzzer, "FAULT outputs safe");
    in = nominal(t, T); o = scm_step(&c, &in); t += 100;
    CHECK(c.state == ST_FAULT, "fault is latched without reset");
    in = nominal(t, T); in.cmd_reset = true; o = scm_step(&c, &in); t += 100;
    CHECK(c.state == ST_SELFTEST, "reset with cause cleared -> SELFTEST");
    /* 3 thermocouple trip */
    scm_init(&c); t = 0; T = 250; run_to_ready(&c, &t, &T);
    in = nominal(t, SCM_T_TRIP_DC); o = scm_step(&c, &in);
    CHECK(c.state == ST_FAULT && (c.fault_flags & F_T_TRIP), "T_TRIP -> FAULT");
    in = nominal(t, SCM_T_WARN_DC + 10); in.cmd_reset = true; o = scm_step(&c, &in);
    CHECK(c.state == ST_FAULT, "no reset while hotter than warn temperature");
    /* 4 open control thermocouple */
    scm_init(&c); t = 0; T = 250; run_to_ready(&c, &t, &T);
    in = nominal(t, T); in.tc_fault_mask = 0x01; o = scm_step(&c, &in);
    CHECK(c.fault_flags & F_TC_OPEN, "open control TC -> FAULT");
    /* 5 over-current, 6 e-stop, 7 stale data */
    scm_init(&c); t = 0; T = 250; run_to_ready(&c, &t, &T);
    in = nominal(t, T); in.current_ma = SCM_I_MAX_MA + 1; scm_step(&c, &in);
    CHECK(c.fault_flags & F_OVERCURRENT, "over-current -> FAULT");
    scm_init(&c); t = 0; T = 250; run_to_ready(&c, &t, &T);
    in = nominal(t, T); in.estop_open = true; o = scm_step(&c, &in);
    CHECK((c.fault_flags & F_ESTOP) && !o.heat_en, "E-stop -> FAULT, heater off");
    scm_init(&c); t = 0; T = 250; run_to_ready(&c, &t, &T);
    for (int i = 0; i < 7; i++) { in = nominal(t, T); in.data_fresh = false; scm_step(&c, &in); t += 100; }
    CHECK(c.fault_flags & F_STALE, "stale sensor data -> FAULT");
    /* 8 heating faster than the ramp limit (e.g. SSR stuck on) */
    scm_init(&c); t = 0; T = 250;
    for (int i = 0; i < 25; i++) { in = nominal(t, T); in.cmd_start = (i > 20); scm_step(&c, &in); t += 100; }
    for (int i = 0; i < 700 && c.state != ST_FAULT; i++) { in = nominal(t, T); scm_step(&c, &in); t += 100; T += 2; }  /* 12 C/min */
    CHECK(c.fault_flags & F_RAMP, "ramp > limit -> FAULT");
    /* 9 low voltage only enforced while READY; room-temperature cell (insulator) does not trip */
    scm_init(&c); t = 0; T = 250;
    in = nominal(t, T); in.cell_mv[0] = 0; scm_step(&c, &in);
    CHECK(c.state != ST_FAULT, "cold cell at 0 V does not trip");
    scm_init(&c); t = 0; T = 250; run_to_ready(&c, &t, &T);
    in = nominal(t, T); in.cell_mv[0] = SCM_V_TRIP_LOW_MV - 1; scm_step(&c, &in);
    CHECK(c.fault_flags & F_V_LOW, "V_LOW in READY -> FAULT");
    /* 10 limits consistent with chemistry side reactions (1.58 V / 3.05 V) */
    CHECK(SCM_V_TRIP_HIGH_MV < 3050 && SCM_V_TRIP_LOW_MV > 1580, "trips inside the over-charge/over-discharge reaction voltages");
    CHECK(SCM_V_CHARGE_MAX_MV < SCM_V_TRIP_HIGH_MV && SCM_V_DISCHARGE_MIN_MV > SCM_V_TRIP_LOW_MV, "operating window inside trips");
    printf("%d checks, %d failures\n", checks, fails);
    return fails ? 1 : 0;
}
