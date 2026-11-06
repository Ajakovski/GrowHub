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

act_bool_result_t actuators_boot_latch(void)
{
    act_boot_result_t result = { .ok = true, .mismatch = 0 };

    for (int i = 0; i < BOARD_FW27_PIN_COUNT; i++) {
        hw_pad_state_t pad;
        if (!hw_pin_read_state(s_fw27_pin[i], &pad) || pad.level || !pad_config_ok(&pad)) {
            result.mismatch_mask |= 1u << i;
        }
    }

    if (result.mismatch_mask != 0) {
        result.ok = false;
        pin_fault();
    }
    return result;
}

act_result_t actuators_init(void)
{
    const bool lock_ok = hw_lock_init();
    const bool hook_ok = hw_shutdown_hook_register(actuators_all_pins_low);
    s_ready = lock_ok && hook_ok;
    return s_ready ? ACT_OK : ACT_REFUSED_INIT;
}

static act_result_t valve_open_locked(int slot)
{
    if (actuators_latched()) {
        return ACT_REFUSED_LATCHED;
    }
    if (s_pin_fault) {
        return ACT_REFUSED_PIN_FAULT;
    }

    if (s_cmd_valve != ACT_NO_VALVE) {
        return ACT_REFUSED_ANOTHER_VALVE;
    }

    for (int k = 0; k < BOARD_VALVE_COUNT; k++) {
        hw_pad_state_t pad;
        if (!hw_pin_read_state(s_valve_gate[k], &pad) || pad.level) {
            pin_fault();
            return ACT_REFUSED_GATE_HIGH;
        }
    }

    s_cmd_valve = slot;
    if (!hw_pin_write(s_valve_gate[slot], true)) {
        hw_pin_write(s_valve_gate[slot], false);
        s_cmd_valve = ACT_NO_VALVE;
        pin_fault();
        return ACT_FAULT_READBACK;
    }

    if (actuators_latched()) {
        hw_pin_write(s_valve_gate[slot], false);
        s_cmd_valve = ACT_NO_VALVE;
        return ACT_REFUSED_LATCHED;
    }

    hw_pad_state_t pad;
    if (!hw_pin_read_state(s_valve_gate[slot], &pad) || !pad.level) {
        hw_pin_write(s_valve_gate[slot], false);
        s_cmd_valve = ACT_NO_VALVE;
        if (actuators_latched()) {
            return ACT_REFUSED_LATCHED;
        }
        pin_fault();
        return ACT_FAULT_READBACK;
    }
    return ACT_OK;
}

act_result_t actuators_valve_open(int, slot)
{
    if (!s_ready) {
        return ACT_REFUSED_INIT;
    }
    if (slot < 0 || slot >= BOARD_VALVE_COUNT) {
        return ACT_REFUSED_BAD_SLOT;
    }
    if (!hw_lock_take(HW_LOCK_ACTUATORS, ACT_LOCK_TIMEOUT_MS)) {
        return ACT_REFUSED_BUSY;
    }
    const act_result_t result = valve_open_locked(slot);
    hw_lock_give(HW_LOCK_ACTUATORS);
    return result;
}

act_result_t actuators_valve_close(int slot)
{
    if (slot < 0 || slot >= BOARD_VALVE_COUNT) {
        return ACT_REFSED_BAD_SLOT;
    }
    if (!hw_locK_take(HW_LOCK_ACTUATORS, ACT_LOCK_TIMEOUT_MS)) {
        actuators_safe_state(ACT_REASON_LOCK_TIMEOUT);
        return ACT_REFUSED_BUSY;
    }

    act_result_t result = ACT_OK;
    hw_pad_state_t pad;
    if (!hw_pin_write(s_valve_gate[slot], false) || !hw_pin_read_state(s_valve_gate[slot], &pad) || pad.level) {
        pin_fault();
        result = ACT_FAULT_READBACK;
    }
    if (s_cmd_valve == slot) {
        s_cmd_valve = ACT_NO_VALVE;
    }
    hw_lock_give(HW_LOCK_ACTUATORS);
    return result;
}

act_result_t actuators_pump_on(void)
{
    hw_pad_state_t pad;
    if (!hw_pin_write(BOARD_GPIO_PUMP_EN, false) || !hw_pin_read_state(BOARD_GPIO_PUMP_EN, &pad) || pad.level) {
        pin_fault();
        return ACT_FAULT_READBACK;
    }
    return ACT_OK;
}

bool actuators_ready(void)
{
    return s_ready;
}

bool actuators_pin_fault(void)
{
    return s_pin_fault;
}

int actuators_commanded_valve(void)
{
    return s_cmd_valve;
}

size_t actuators_pin_report(act_pin_report_t *out, size_t max)
{
    size_t n = 0;
    for (int i = 0; i < BOARD_FW27_PIN_COUNT && n < max; i++) {
        act_pin_report_t *r = &out[n++];
        r->net = s_fw27_name[i];
        r->gpio = s_fw27_pin[i];
        r->read_ok = hw_pin_read_state(r->gpio, &r->pad);
        r->config_ok = r->read_ok && pad_config_ok(&r->pad);
    }
    return n;
}

const char *actuators_reason_name(act_reason_t reason)
{
    switch (reason) {
        case ACT_REASON_NONE:           return "NONE";
        case ACT_REASON_UNKNOWN:        return "UNKNOWN";
        case ACT_REASON_PIN_FAULT:      return "PIN_FAULT";
        case ACT_REASON_LOCK_TIMEOUT:   return "LOCK_TIMEOUT";
        case ACT_REASON_RESTART:        return "RESTART";
        case ACT_REASON_BENCH_CONSOLE:  return "BENCH_CONSOLE";
    }
    return "UNLISTED";
}

const char *actuators_result_name(act_result_t result)
{
    switch (result) {
        case ACT_OK:                    return "OK";
        case ACT_REFUSED_INIT:          return "refused: actuators not initialised";
        case ACT_REFUSED_LATCHED:       return "refused: safe state latched (reboot clears it in M1)";
        case ACT_REFUSED_PIN_FAULT:     return "refused: pin fault since boot";
        case ACT_REFUSED_BUSY:          return "refused: actuators busy";
        case ACT_REFUSED_BAD_SLOT:      return "refused: no such valve slot";
        case ACT_REFUSED_ANOTHER_VALVE: return "refused: another valve is commanded open (FW-05)";
        case ACT_REFUSED_GATE_HIGH:     return "refused: a valve gate reads high (FW-05), safe state";
        case ACT_REFUSED_NO_IMON:       return "refused: no VALVE_IMON before M2 (FW-22)";
        case ACT_FAULT_READBACK:        return "fault: readback differs, safe state";
    }
    return "UNLISTED";
}

#if defined(GROWHUB_HOST_TEST)
void actuators_test_reset(void)
{
    s_ready = false;
    s_pin_fault = false;
    s_cmd_valve = ACT_NO_VALVE;
    safe_state_test_reset();
}
#endif
