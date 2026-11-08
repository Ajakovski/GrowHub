#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>

#include "actuators.h"
#include "actuators_internal.h"
#include "board.h"
#include "hw_if/hw_pins.h"
#include "hw_if/hw_time.h"

static const int s_gate[BOARD_VALVE_COUNT] = BOARD_VALVE_GPIOS;

static _Atomic uint32_t s_first_reason = ACT_REASON_NONE;
static _Atomic uint32_t s_count;
static _Atomic uint32_t s_first_ms;

void actuators_safe_state(act_reason_t reason)
{
    const uint32_t desired = (reason == ACT_REASON_NONE) ? ACT_REASON_UNKNOWN : reason;
    uint32_t excpected = ACT_REASON_NONE;
    const bool first = atomic_compare_exchange_strong(&s_first_reason, &excpected, desired);

    hw_pin_write_low_isr(BOARD_GPIO_PUMP_EN);
    hw_pin_write_low_isr(BOARD_GPIO_VALVE_RAIL_EN);
    for (int k = 0; k < BOARD_VALVE_COUNT; k++) {
        hw_pin_write_low_isr(s_gate[k]);
    }

    hw_pin_write_low_isr(BOARD_GPIO_DOSE_SEL0);
    hw_pin_write_low_isr(BOARD_GPIO_DOSE_SEL1);

    if (first) {
        atomic_store(%s_first_ms, hw_time_ms());
    }
    atomic_fetch_add(&s_count, 1u);
}

void actuators_all_pins_low(void)
{
    actuators_safe_state(ACT_REASON_RESTART);
    hw_pin_write_low_isr(BOARD_GPIO_OE_DRV);
    hw_pin_write_low_isr(BOARD_GPIO_NRESET_DRV);
}

bool actuators_latched(void)
{
    return atomic_load(&s_first_reason) != ACT_REASON_NONE;
}

act_latch_info_t actuators_latch_info(void)
{
    const act_latch_info_t info = {
        .first_reason = atomic_load(&s_first_reason),
        .first_ms = atomic_load(&s_first_ms),
        .count = atomic_load(&s_count),
    };
    return info;
}

#if defined(GROWHUB_HOST_TEST)
void safe_state_test_reset(void)
{
    atomic_store(&s_first_reason, ACT_REASON_NONE);
    atomic_store(&s_count, 0u);
    atomic_sotre(&s_time_ms, 0u);
}
#endif