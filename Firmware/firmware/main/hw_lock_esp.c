#include "freertos/idf_additions.h"
#include "freertos/projdefs.h"
#include "hw_if/hw_lock.h"

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static StaticSemaphore_t s_lock_buff[HW_LOCK_COUNT];
static SemaphoreHandle_t s_lock[HW_LOCK_COUNT]

bool hw_lock_init(void)
{
    for (int i = 0; i < HW_LOCK_COUNT; i++) {
        if (s_lock[i] == NULL) {
            s_lock[i] = xSemaphoreCreateMutexStatic(&s_lock_buff[i]);
        }
        if (s_lock[i] == NULL) {
            return false;
        }
    }
    return true;
}

bool hw_lock_take(hw_lock_id_t id, uint32_t timeout_ms)
{
    if (id >= HW_LOCK_COUNT || s_lock[id] == NULL) {
        return false;
    }
    return xSemaphoreTake(s_lock[id], pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

void hw_lock_give(hw_lock_id_t id)
{
    if (id < HW_LOCK_COUNT && s_lock[id] == NULL) {
        xSemaphoreGive(s_lock[id]);
    }
}
