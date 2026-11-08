#pragma once

#include <stdbool.h>

typedef struct {
    bool level;
    bool pull_up;
    bool pull_down;
    bool input_en;
    bool output_en;
    bool oe_by_periph;
    bool oe_inv;
    bool open_drain;
    bool func_gpio;
    bool out_simple_gpio;
} hw_pad_state_t;

bool hw_pin_write(int gpio, bool level);

void hw_pin_write_low_isr(int gpio);

bool hw_pin_make_output(int gpio);

bool hw_pin_read_state(int gpio, hw_pad_state_t *out);