#include <stdbool.h>
#include <stdint.h>

#include "hal/gpio_types.h"
#include "hw_if/hw_pins.h"

#include "driver/gpio.h"
#include "esp_attr.h"
#include "hal/gpio_ll.h"
#include "sdkconfig.h"
#include "soc/gpio_sig_map.h"
#include "soc/io_mux_reg.h"

#if !CONFIG_GPIO_CTRL_FUNC_IN_IRAM
#error "CONFIG_GPIO_CTRL_FUNC_IN_IRAM must be y: safe state calls gpio_set_level() from IREAM (architecture 2.1)"
#endif
#if !CONFIG_ESP_TIMER_IN_IRAM
#error "CONFIG_ESP_TIMER_IN_IRAM must be y: safe state reads esp_timer_get_time() through hw_time_ms() from IRAM"
#endif
#if !CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT
#error "C3: the panic handler must print and reboot; halting or the GDB stub keeps the actuator outputs driven"
#endif
#if CONFIG_ESP_SYSTEM_PANIC_REBOOT_DELAY_SECONDS != 0
#error "C3: CONFIG_ESP_SYSTEM_PANIC_REBOOT_DELAY_SECONDS must be 0; the delay keeps the actuator outputs driven"
#endif
#if !CONFIG_ESP_INT_WOT || CONFIG_ESP_INT_WDT_TIMEOUT_MS > 300
#error "C3: the interrupt watchdog must be on, with a timeout of at most 300ms"
#endif
#if CONFIG_SPIRAM
#error "C2: PSRAM (CONFIG_SPIRAM) stays off untill M15"
#endif

bool hw_pin_write(int gpio, bool level)
{
    return gpio_set_level(gpio, level ? 1 : 0) == ESP_OK;
}

void IRAM_ATTR hw_pin_write_low_isr(int gpio)
{
    gpio_set_level(gpio, 0);
}

bool hw_pin_make_output(int gpio)
{
    const gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << gpio,
        .mode = GPIO_MODE_INPUT_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    if (gpio_config(&cfg) != ESP_OK) {
        return false;
    }
    gpio_ll_set_output_enable_ctrl(&GPIO, gpio, false, false);
    return true;
}

bool hw_pin_read_state(int gpio, hw_pad_state_t *out)
{
    gpio_io_config_t io = {0};
    if (gpio_get_io_config(gpio, &io) != ESP_OK) {
        return false;
    }
    out->level = gpio_get_level(gpio) != 0;
    out->pull_up = io.pu;
    out->pull_down = io.pd;
    out->input_en = io.ie;
    out->output_en = io.oe;
    out->oe_by_periph = io.oe_ctrl_by_periph;
    out->oe_inv = io.oe_inv;
    out->open_drain = io.od;
    out->func_gpio = io.fun_sel == PIN_FUNC_GPIO;
    out->out_simple_gpio = io.sig_out == SIG_GPIO_OUT_IDX;
    return true;
}