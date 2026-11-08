#pragma once

#include <stdbool.h>

bool hw_shutdown_hook_register(void (*hook)(void));