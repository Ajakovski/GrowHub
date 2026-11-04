# All firmware sources live in main/. Add every new .c file to SRCS,
# then run `idf.py reconfigure` so Zed picks it up.
idf_component_register(SRCS "main.c"
                            "actuators.c"
                            "actuators_pins_esp.c"
                            "safe_state.c"
                            "bench_console.c"
                            "hw_lock_esp.c"
                            "hw_system_esp.c"
                            "hw_time_esp.c"
                       INCLUDE_DIRS "."
                       PRIV_REQUIRES esp_driver_gpio esp_hal_gpio soc
                       LDFRAGMENTS "linker.lf")

target_compile_options(${COMPONENT_LIB} PRIVATE
                       -Werror=unused-function -Werror=unused-variable -Werror=unused-but-set-variable
                       -Werror=deprecated-declarations -Werror=extra)
