/* SCM-1 supervision core - see scm_core.h. CONCEPT firmware rev A 2026-11-02. */
#include "scm_core.h"
#include <stddef.h>

#define TICK_MS            100u
#define SELFTEST_MS        2000u
#define STALE_TICKS_MAX    5u            /* 0.5 s without fresh data -> fault */
#define RAMP_WINDOW_MS     60000u        /* measured ramp evaluated over 1 min */
#define RAMP_MARGIN_DC     30            /* allow +3 C/min above the commanded ramp before tripping */
#define READY_BAND_DC      50            /* within 5 C of set point -> READY */

const char *scm_state_name(scm_state_t s) {
    static const char *n[] = {"BOOT", "SELFTEST", "HEATUP", "READY", "COOLDOWN", "FAULT"};
    return (s <= ST_FAULT) ? n[s] : "?";
}

void scm_init(SCM_Core *c) {
    c->state = ST_BOOT; c->fault_flags = 0; c->t_state_ms = 0; c->setpoint_dc = 250;   /* 25 C */
    c->have_prev = false; c->t_prev_dc = 0; c->t_prev_ms = 0; c->ctrl_tc_dc = 0; c->stale_count = 0; c->ramp_acc = 0;
}

uint32_t scm_check_limits(const SCM_Core *c, const SCM_Inputs *in) {
    uint32_t f = 0;
    uint8_t n = in->n_cells > SCM_N_CELLS ? SCM_N_CELLS : in->n_cells;
    /* voltage trips only matter once the cell is molten/operating; at room temperature the cell is an insulator */
    bool hot = in->tc_dc[0] >= SCM_T_MIN_DC - 100;
    for (uint8_t k = 0; k < n && hot; k++) {
        if (in->cell_mv[k] >= SCM_V_TRIP_HIGH_MV) f |= F_V_HIGH;
        if (c->state == ST_READY && in->cell_mv[k] <= SCM_V_TRIP_LOW_MV) f |= F_V_LOW;
    }
    for (int k = 0; k < 4; k++) if (in->tc_dc[k] >= SCM_T_TRIP_DC) f |= F_T_TRIP;
    if (in->tc_fault_mask & 0x01u) f |= F_TC_OPEN;                       /* control TC must always be valid */
    if (in->tc_fault_line_low) f |= F_T_TRIP;                            /* hardware line already cut the heater */
    if (in->current_ma > SCM_I_MAX_MA || in->current_ma < -SCM_I_MAX_MA) f |= F_OVERCURRENT;
    if (in->estop_open) f |= F_ESTOP;
    return f;
}

static void enter(SCM_Core *c, scm_state_t s, uint32_t t) { c->state = s; c->t_state_ms = t; c->ramp_acc = 0; }

SCM_Outputs scm_step(SCM_Core *c, const SCM_Inputs *in) {
    SCM_Outputs o = {0};
    uint32_t t = in->t_ms;
    c->ctrl_tc_dc = in->tc_dc[0];
    c->stale_count = in->data_fresh ? 0 : c->stale_count + 1;
    uint32_t f = scm_check_limits(c, in);
    if (c->stale_count > STALE_TICKS_MAX) f |= F_STALE;
    /* measured heating rate over a 1-minute window (protects beta''-alumina and the glass seal) */
    if (!c->have_prev) { c->t_prev_dc = in->tc_dc[0]; c->t_prev_ms = t; c->have_prev = true; }
    else if (t - c->t_prev_ms >= RAMP_WINDOW_MS) {
        int32_t rate = (int32_t)((int64_t)(in->tc_dc[0] - c->t_prev_dc) * 60000 / (int64_t)(t - c->t_prev_ms));
        if (rate > SCM_RAMP_DC_PER_MIN + RAMP_MARGIN_DC || rate < -(SCM_RAMP_DC_PER_MIN + RAMP_MARGIN_DC)) f |= F_RAMP;
        c->t_prev_dc = in->tc_dc[0]; c->t_prev_ms = t;
    }
    /* heater read-back must agree with what the hardware AND gate should be doing (after one tick of settling) */
    if (c->state != ST_BOOT && c->state != ST_FAULT) {
        bool expected = (c->state == ST_HEATUP || c->state == ST_READY) && !in->tc_fault_line_low && in->tc_dc[0] < c->setpoint_dc;
        if (in->heater_fb_on && !expected && in->tc_dc[0] > c->setpoint_dc + 100) f |= F_HEATER_FB;   /* stuck-on SSR */
    }
    if (f && c->state != ST_FAULT) { c->fault_flags |= f; enter(c, ST_FAULT, t); }

    switch (c->state) {
    case ST_BOOT:
        enter(c, ST_SELFTEST, t); break;
    case ST_SELFTEST:
        if (!in->data_fresh) { c->fault_flags |= F_SELFTEST; enter(c, ST_FAULT, t); break; }
        if (t - c->t_state_ms >= SELFTEST_MS && in->cmd_start) { c->setpoint_dc = in->tc_dc[0]; enter(c, ST_HEATUP, t); }
        break;
    case ST_HEATUP: {
        /* 2 C/min = 0.033 deci-degC per 100 ms tick -> integer accumulator */
        c->ramp_acc += SCM_RAMP_DC_PER_MIN * TICK_MS;
        while (c->ramp_acc >= 60000u && c->setpoint_dc < SCM_T_SET_DC) { c->setpoint_dc++; c->ramp_acc -= 60000u; }
        if (c->setpoint_dc >= SCM_T_SET_DC && in->tc_dc[0] >= SCM_T_SET_DC - READY_BAND_DC) enter(c, ST_READY, t);
        if (in->cmd_stop) enter(c, ST_COOLDOWN, t);
        break; }
    case ST_READY:
        if (in->cmd_stop) enter(c, ST_COOLDOWN, t);
        break;
    case ST_COOLDOWN: {
        c->ramp_acc += SCM_RAMP_DC_PER_MIN * TICK_MS;
        while (c->ramp_acc >= 60000u && c->setpoint_dc > 250) { c->setpoint_dc--; c->ramp_acc -= 60000u; }
        if (in->cmd_start && in->tc_dc[0] > SCM_T_MIN_DC) enter(c, ST_HEATUP, t);
        break; }
    case ST_FAULT:
        /* latched: only an operator reset with the cause cleared and the cell below the warn temperature releases it */
        if (in->cmd_reset && f == 0 && in->tc_dc[0] < SCM_T_WARN_DC) { c->fault_flags = 0; enter(c, ST_SELFTEST, t); }
        break;
    }
    o.setpoint_dc = c->setpoint_dc;
    o.heat_en = (c->state == ST_HEATUP || c->state == ST_READY || c->state == ST_COOLDOWN) && in->tc_dc[0] < c->setpoint_dc;
    o.interlock_closed = (c->state == ST_READY);
    o.buzzer = (c->state == ST_FAULT);
    o.led_fault = (c->state == ST_FAULT);
    o.led_run = (c->state == ST_READY) || ((t / 500u) & 1u);
    if (c->state == ST_FAULT) { o.heat_en = false; o.interlock_closed = false; }
    return o;
}
