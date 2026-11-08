#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    HW_LOCK_ACTUATORS = 0,
    HW_LOCK_COUNT,
} hw_lock_id_t;

bool hw_lock_init(void);

bool hw_lock_take(hw_lock_id_t id, uint32_t timeout_ms);

void hw_lock_give(hw_lock_id_t id);