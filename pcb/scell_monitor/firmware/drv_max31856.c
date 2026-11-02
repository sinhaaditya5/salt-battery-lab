#include "drv_max31856.h"
#include "hal.h"
int16_t max31856_threshold_code(int32_t t_dc) { return (int16_t)((t_dc * 16) / 10); }          /* 0.0625 C/LSB */
int32_t max31856_temp_from_raw(uint32_t raw24) {                                              /* raw = LTCBH:M:L */
    int32_t v = (int32_t)(raw24 << 8) >> 13;                                                  /* sign-extend 19-bit */
    return (v * 10) / 128;                                                                    /* 1/128 C/LSB -> dC */
}
static void wr(uint8_t cs, uint8_t reg, uint8_t val) { uint8_t tx[2] = {(uint8_t)(reg | MAX31856_WRITE), val}, rx[2]; hal_spi_xfer(cs, tx, rx, 2); }
void max31856_init(max31856_t *d, uint8_t cs, int32_t trip_dc) {
    d->cs = cs;
    int16_t code = max31856_threshold_code(trip_dc);
    wr(cs, MAX31856_REG_CR1, 0x03);                         /* type K, 1 sample */
    wr(cs, MAX31856_REG_MASK, 0x00);                        /* all faults drive ~FAULT */
    wr(cs, MAX31856_REG_LTHFTH, (uint8_t)((uint16_t)code >> 8));
    wr(cs, MAX31856_REG_LTHFTL, (uint8_t)(code & 0xFF));
    wr(cs, MAX31856_REG_CR0, 0x80 | 0x10 | 0x01);          /* auto conversion, open-circuit detect, 50 Hz (India mains) */
}
bool max31856_read(max31856_t *d, int32_t *t_dc, uint8_t *status) {
    uint8_t tx[5] = {MAX31856_REG_LTCBH, 0, 0, 0, 0}, rx[5] = {0};
    hal_spi_xfer(d->cs, tx, rx, 5);                         /* LTCBH, LTCBM, LTCBL, SR (auto-increment) */
    uint32_t raw = ((uint32_t)rx[1] << 16) | ((uint32_t)rx[2] << 8) | rx[3];
    *t_dc = max31856_temp_from_raw(raw); *status = rx[4];
    return (rx[4] & 0x01u) == 0;                            /* OPEN fault -> false */
}
