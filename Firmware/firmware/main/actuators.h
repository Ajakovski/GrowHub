#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "board.h"
#include "hw_if/hw_pins.h"

#define ACTUATORS_PIN_COUNT BOARD_FW27_PIN_COUNT
#define ACT_NO_VALVE        (-1)

typedef enum {
    ACT_REASON_NONE = 0,
    ACT_REASON_UNKNOWN,
    ACT_REASON_PIN_FAULT,
    ACT_REASON_LOCK_TIMEOUT,
    ACT_REASON_RESTART,
    ACT_REASON_BENCH_CONSOLE,
} act_reason_t;

typedef enum {
    ACT_OK = 0,
    ACT_REFUSED_INIT,
    ACT_REFUSED_LATCHED,
    ACT_REFUSED_PIN_FAULT,
    ACT_REFUSED_BUSY,
    ACT_REFUSED_BAD_SLOT,
    ACT_REFUSED_ANOTHER_VALVE,
    ACT_REFUSED_GATE_HIGH,
    ACT_REFUSED_NO_IMON,
    ACT_FAULT_READBACK,
} act_result_t;

typedef struct {
    bool ok;
    uint32_t mismatch_mask;
} act_bool_result_t;

typedef struct {
    act_reason_t first_reason;
    uint32_t first_ms;
    uint32_t count;
} act_latch_info_t;

typedef struct {
    const char *net;
    int gpio;
    bool read_ok;
    hw_pad_state_t pad;
    bool config_ok;
} act_pin_report_t;

act_boot_result_t actuators_boot_latch(void);

act_result_t actuators_init(void);

void actuators_safe_state(act_reason_t reason);

bool actuators_latched(void);
act_latch_info_t actuators_latch_info(void);

act_result_t actuators_valve_open(int slot);
act_result_t actuators_valve_close(int slot);

act_result_t actuators_pump_on(void);
act_result_t actuators_pump_off(void);

bool actuators_ready(void);
bool actuators_pin_fault(void);
int actuators_commanded_valve(void);

size_t actuators_pin_report(act_pin_report_t *out, size_t max);

const char *actuators_reason_name(act_reason_t reason);
const char *actuators_result_name(act_result_t result);