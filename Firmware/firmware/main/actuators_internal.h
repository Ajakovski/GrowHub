#pragma once

void actuators_all_pins_low(void);

#if defined(GROWHUB_HOST_TEST)
void actuators_test_reset(void);
void safe_state_test_reset(void);
#endif