#include "hw_if/hw_time.h"

#include "esp_attr.h"
#include "esp_timer.h"
#include <stdint.h>

uint32_t IRAM_ATTR hw_time_ms(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000);
}