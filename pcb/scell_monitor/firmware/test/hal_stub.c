#include "../hal.h"
void hal_spi_xfer(uint8_t cs, const uint8_t *tx, uint8_t *rx, uint16_t n) { (void)cs; (void)tx; for (uint16_t i = 0; i < n; i++) rx[i] = 0; }
