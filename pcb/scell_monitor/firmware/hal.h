/* SCM-1 hardware abstraction. Implemented for STM32G474 in hal_stm32.c (NOT YET WRITTEN - needs STM32CubeG4 + board).
 * Pin map is fixed by pcb/scell_monitor/design_scm.py (used{} dict). */
#ifndef SCM_HAL_H
#define SCM_HAL_H
#include <stdint.h>
#include <stdbool.h>
uint32_t hal_millis(void);
void hal_watchdog_kick(void);                       /* IWDG, 500 ms window: a hung loop opens K1 and drops HEAT_EN */
/* SPI1 shared: ADS131M08 (CS=PB12), MAX31856 x4 (CS=PB13,PB14,PB15,PC7). Mode 1, <=5 MHz. */
void hal_spi_xfer(uint8_t cs_index, const uint8_t *tx, uint8_t *rx, uint16_t n);   /* cs_index 0=ADC, 1..4=TC */
/* I2C3 (PC8/PC9): INA228 at 0x40 */
bool hal_i2c_read16(uint8_t addr, uint8_t reg, uint16_t *v);
bool hal_i2c_read24(uint8_t addr, uint8_t reg, uint32_t *v);
bool hal_i2c_write16(uint8_t addr, uint8_t reg, uint16_t v);
/* GPIO */
bool hal_tc_fault_line_low(void);                   /* PB1 */
bool hal_estop_open(void);                          /* PC12 (high = loop open) */
bool hal_heater_fb_on(void);                        /* PA0 (low = SSR drive on) */
void hal_set_heat_en(bool on);                      /* PB4 -> 74LVC1G08 */
void hal_set_interlock(bool closed);                /* PB5 -> TPL7407 -> K1 */
void hal_set_buzzer(bool on);                       /* PB0 */
void hal_set_leds(bool run, bool fault);            /* PB6, PB7 */
/* USART1 via ISO7721 -> FT230X: 115200 8N1 CSV log + single-letter commands (S=start, X=stop, R=reset) */
void hal_uart_write(const char *s);
int  hal_uart_getc(void);                           /* -1 if none */
#endif
