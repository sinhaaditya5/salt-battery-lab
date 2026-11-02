#include <stdio.h>
#include "../drv_max31856.h"
int main(void) {
    int f = 0;
    if (max31856_threshold_code(2900) != 4640) { printf("FAIL threshold code %d\n", max31856_threshold_code(2900)); f++; }   /* 290.0 C / 0.0625 */
    uint32_t raw = (uint32_t)(190 * 128) << 5;                       /* 190 C in 19-bit left-justified in 24 */
    if (max31856_temp_from_raw(raw) != 1900) { printf("FAIL temp %ld\n", (long)max31856_temp_from_raw(raw)); f++; }
    uint32_t neg = ((uint32_t)(-10 * 128) & 0x7FFFFu) << 5;          /* -10 C */
    if (max31856_temp_from_raw(neg) != -100) { printf("FAIL neg temp %ld\n", (long)max31856_temp_from_raw(neg)); f++; }
    printf("driver conversions: %d failures\n", f);
    return f;
}
