/*
 * actuators: FW-27 boot launch, init, valve and pump API, readback.
 * 
 * Plain C on hw_if (no ESP-IDF headers), so test/host builds and tests this same file. Safe state and its latch
 * live in safe_state.c, which linker.lf places in IRAM. 
 */
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "actuators.h"
#include "actuators_internal.h"
#include "board.h"
#include "hw_if/hw_lock.h"
#include "hw_if/hw_pins.h"
#include "hw_if/hw_system.h"

/* Bounded wait for the actuators lock [Guessing: far above the longest hold, a handful of register accsesses;
 * 5 ticks at the default 100 Hz] */
#define ACT_LOCK_TIMEOUT_MS 50u

static const int s_fw27_pin[BOARD_FW27_PIN_COUNT] = BOARD_FW27_PINS;
static const char *const s_fw27_name[BOARD_FW27_PIN_COUNT] = BOARD_FW27_PIN_NAMES;
static const int s_valve_gate[BOARD_VALVE_COUNT] = BOARD_VALVE_GPIOS;

static_assert(BOARD_FW27_PIN_COUNT <= 32, "mismatch_mask has one bit per FW-27 pin");

static bool s_ready;
static bool s_pin_fault;
static int s_cmd_valve = ACT_NO_VALVE;

static bool pad_config_ok(const hw_pad_state_t *p)
{
    return p->output_en && !p->oe_by_periph && !p->oe_inv && p->input_en && !p->pull_up && !p->pull_down &&
    !p->open_drain && p->func_gpio && p->out_simple_gpio;
}

static void pin_fault(void)
{
    s_pin_fault = true;
    actuators_safe_state(ACT_REASON_PIN_FAULT);
}
