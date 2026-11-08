#include "hw_if/hw_system.h"

#include "esp_system.h"

bool hw_shutdown_hook_register(void (*hook)(void))
{
    return esp_register_shutdown_handler(hook) == ESP_OK;
}