/* SCM-1 target main loop (10 Hz). Requires hal_stm32.c + ADS131M08/INA228 drivers - NOT YET WRITTEN.
 * Compiles on the host with -DSCM_HOST_SYNTAX_CHECK (make syntax) to catch interface drift. */
#include <stdio.h>
#include "scm_core.h"
#include "hal.h"
#include "drv_max31856.h"
extern bool adc_read_cells(int32_t mv[SCM_N_CELLS]);      /* ADS131M08: calibrated adjacent-tap differentials */
extern bool ina228_read_current_ma(int32_t *ma);
#ifndef SCM_HOST_SYNTAX_CHECK
int main(void)
#else
int scm_target_main(void)
#endif
{
    SCM_Core core; scm_init(&core);
    max31856_t tc[4];
    for (uint8_t k = 0; k < 4; k++) max31856_init(&tc[k], (uint8_t)(k + 1), SCM_T_TRIP_DC);
    uint32_t next = hal_millis();
    for (;;) {
        while ((int32_t)(hal_millis() - next) < 0) { }
        next += 100;
        SCM_Inputs in = {0}; in.t_ms = hal_millis(); in.n_cells = SCM_N_CELLS; bool ok = true;
        for (int k = 0; k < 4; k++) { uint8_t st; if (!max31856_read(&tc[k], &in.tc_dc[k], &st)) in.tc_fault_mask |= (uint8_t)(1u << k); }
        ok &= adc_read_cells(in.cell_mv); ok &= ina228_read_current_ma(&in.current_ma);
        in.tc_fault_line_low = hal_tc_fault_line_low(); in.estop_open = hal_estop_open(); in.heater_fb_on = hal_heater_fb_on(); in.data_fresh = ok;
        int ch = hal_uart_getc(); in.cmd_start = (ch == 'S'); in.cmd_stop = (ch == 'X'); in.cmd_reset = (ch == 'R');
        SCM_Outputs o = scm_step(&core, &in);
        hal_set_heat_en(o.heat_en); hal_set_interlock(o.interlock_closed); hal_set_buzzer(o.buzzer); hal_set_leds(o.led_run, o.led_fault);
        char line[160];
        snprintf(line, sizeof line, "%lu,%s,%lx,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%d,%d\r\n", (unsigned long)in.t_ms, scm_state_name(core.state),
                 (unsigned long)core.fault_flags, (long)in.cell_mv[0], (long)in.cell_mv[1], (long)in.tc_dc[0], (long)in.tc_dc[1],
                 (long)in.current_ma, (long)o.setpoint_dc, (long)in.tc_dc[2], o.heat_en, o.interlock_closed);
        hal_uart_write(line);
        hal_watchdog_kick();
    }
}
