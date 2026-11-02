/* SCM-1 safety/supervision core - hardware-independent, unit-tested on the host (test/test_core.c).
 * CONCEPT firmware, rev A 2026-11-02. Not run on target hardware yet (no board exists).
 *
 * The core never touches registers. hal.h feeds it one SCM_Inputs sample per tick (10 Hz) and applies SCM_Outputs.
 * Safety layering (see PROJECT_SALT/07_BUILD_MANUAL/safety):
 *   L1 hardware: heater SSR drive = HEAT_EN AND TC_FAULT_N (74LVC1G08); bimetal cut-out + E-stop in series off-board.
 *   L2 firmware (this file): latched FAULT on any trip; heater off + cycler interlock open + buzzer.
 *   L3 cycler: its own V/I limits (set from the same params/scell_params.py values).
 */
#ifndef SCM_CORE_H
#define SCM_CORE_H
#include <stdint.h>
#include <stdbool.h>
#include "limits.h"

typedef enum { ST_BOOT = 0, ST_SELFTEST, ST_HEATUP, ST_READY, ST_COOLDOWN, ST_FAULT } scm_state_t;

typedef enum {                      /* bit flags, latched in fault_flags */
    F_NONE = 0, F_V_HIGH = 1u << 0, F_V_LOW = 1u << 1, F_T_TRIP = 1u << 2, F_TC_OPEN = 1u << 3, F_RAMP = 1u << 4,
    F_OVERCURRENT = 1u << 5, F_ESTOP = 1u << 6, F_HEATER_FB = 1u << 7, F_SELFTEST = 1u << 8, F_STALE = 1u << 9
} scm_fault_t;

typedef struct {
    uint32_t t_ms;                       /* monotonic time */
    int32_t  cell_mv[SCM_N_CELLS];       /* per-cell voltage, mV (ADS131M08 adjacent-tap differential, calibrated) */
    uint8_t  n_cells;                    /* cells actually connected (1..SCM_N_CELLS) */
    int32_t  tc_dc[4];                   /* thermocouple temperatures, deci-degC */
    uint8_t  tc_fault_mask;              /* bit k set = MAX31856 k reports open / out-of-range */
    bool     tc_fault_line_low;          /* hardware wired-OR FAULT line asserted */
    int32_t  current_ma;                 /* + = charge */
    bool     estop_open;                 /* E-stop loop open */
    bool     heater_fb_on;               /* read-back of SSR drive */
    bool     data_fresh;                 /* all sensors updated this tick */
    bool     cmd_start, cmd_stop, cmd_reset;   /* operator commands (USB) */
} SCM_Inputs;

typedef struct {
    bool heat_en;                        /* request; hardware AND still applies */
    bool interlock_closed;               /* K1 NO-COM: cycler allowed to run */
    bool buzzer;
    bool led_run, led_fault;
    int32_t setpoint_dc;                 /* ramp-limited furnace setpoint */
} SCM_Outputs;

typedef struct {
    scm_state_t state;
    uint32_t fault_flags;
    uint32_t t_state_ms;
    int32_t setpoint_dc;
    int32_t t_prev_dc; uint32_t t_prev_ms; bool have_prev;
    int32_t ctrl_tc_dc;                  /* control thermocouple (TC1) */
    uint32_t stale_count;
    uint32_t ramp_acc;                   /* sub-degree accumulator for the ramp-limited set point */
} SCM_Core;

void scm_init(SCM_Core *c);
SCM_Outputs scm_step(SCM_Core *c, const SCM_Inputs *in);
uint32_t scm_check_limits(const SCM_Core *c, const SCM_Inputs *in);   /* pure: returns fault bits for this sample */
const char *scm_state_name(scm_state_t s);
#endif
