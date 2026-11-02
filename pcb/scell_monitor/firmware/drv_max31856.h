/* MAX31856 thermocouple-to-digital driver (type K). Register map per the Maxim/ADI MAX31856 datasheet -
 * VERIFY against the current datasheet revision before first power-up (checklist TP-E05). */
#ifndef DRV_MAX31856_H
#define DRV_MAX31856_H
#include <stdint.h>
#include <stdbool.h>
#define MAX31856_REG_CR0    0x00u   /* bit7 CMODE auto, bits5:4 OCFAULT, bit1 FAULT mode, bit0 50Hz */
#define MAX31856_REG_CR1    0x01u   /* bits3:0 TC type (K = 0x3), bits6:4 averaging */
#define MAX31856_REG_MASK   0x02u
#define MAX31856_REG_LTHFTH 0x05u   /* linearised-TC high fault threshold, 0.0625 C/LSB, 16-bit signed */
#define MAX31856_REG_LTHFTL 0x06u
#define MAX31856_REG_LTCBH  0x0Cu   /* linearised TC temperature, 19-bit signed, 0.0078125 C/LSB */
#define MAX31856_REG_SR     0x0Fu   /* fault status: bit0 OPEN, bit1 OVUV, bit2 TCLOW, bit3 TCHIGH ... */
#define MAX31856_WRITE      0x80u
typedef struct { uint8_t cs; } max31856_t;
void max31856_init(max31856_t *d, uint8_t cs, int32_t trip_dc);   /* auto-convert, 50 Hz reject, open detect, HI threshold = trip */
bool max31856_read(max31856_t *d, int32_t *t_dc, uint8_t *status); /* returns false on SPI/fault */
int16_t max31856_threshold_code(int32_t t_dc);                     /* exposed for host tests */
int32_t max31856_temp_from_raw(uint32_t raw24);                    /* exposed for host tests */
#endif
