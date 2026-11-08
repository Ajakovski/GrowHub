#pragma once

#include <sdkconfig.h>

#if defined(CONFIG_GROWHUB_REV_A)
#define BOARD_VARIANT_NAME "GROWHUB_REV_A"
#elif defined(CONFIG_BENCH_DEVKITC1)
#define BOARD_VARIANT_NAME "BENCH_DEVKITC1"
#else
#error "No GrowHub board variant selected: set the Kconfig choice GROWHUB_BOARD"
#endif

#define BOARD_GPIO_VALVE_0              1
#define BOARD_GPIO_VALVE_1              2
#define BOARD_GPIO_DOSE_SEL1            3
#define BOARD_GPIO_VALVE_2              9
#define BOARD_GPIO_DOSE_SEL0            10
#define BOARD_GPIO_VALVE_RAIL_EN        38
#define BOARD_GPIO_PUMP_EN              41
#define BOARD_GPIO_OE_DRV               45
#define BOARD_GPIO_NRESET_DRV           46

#define BOARD_GPIO_BOOT                 0
#define BOARD_GPIO_V24_SENSE            4
#define BOARD_GPIO_VALVE_IMON           5
#define BOARD_GPIO_VALVE_RAIL_SENSE_DIV 6
#define BOARD_GPIO_LEAK_BASE            7
#define BOARD_GPIO_RING_DATA            8
#define BOARD_GPIO_OW_F1                11
#define BOARD_GPIO_OW_F2                12
#define BOARD_GPIO_OW_F3                13
#define BOARD_GPIO_LEAK_EXC             14
#define BOARD_GPIO__LOADCELL_DRDY       15
#define BOARD_GPIO_SDA_1                16
#define BOARD_GPIO_SCL_2                17
#define BOARD_GPIO_PWR_ALERT_N          18
#define BOARD_GPIO_MUX_RST_N            21
#define BOARD_GPIO_VIN_FLT_N            39
#define BOARD_GPIO_PG_5V                40
#define BOARD_GPIO_TANK_LOW             42
#define BOARD_GPIO_SDA_0                47
#define BOARD_GPIO_SCL_0                48

#define BOARD_FW27_PIN_COUNT 9
#define BOARD_FW27_PINS 
    {
        BOARD_GPIO_PUMP_EN, BOARD_GPIO_VALVE_RAIL_EN, BOARD_GPIO_VALVE_0,
        BOARD_GPIO_VALVE_1, BOARD_GPIO_VALVE_2, BOARD_GPIO_DOSE_SEL0,
        BOARD_GPIO_DOSE_SEL1, BOARD_GPIO_OE_DRV, BOARD_GPIO_NRESET_DRV,
    }

#define BOARD_FW27_PIN_NAMES
    {
        "PUMP_EN", "VALVE_RAIL_EN", "Valve_0", "Valve_1", "Vavle_2", "DOSE_SEL0",
        "DOSE_SEL_1", "OE_DRV", "nRESET_DRV",
    }

#define BOARD_VALVE_COUNT 3
#define BOARD_VALVE_GPIOS { BOARD_GPIO_VALVE_0, BOARD_GPIO_VALVE_1, BOARD_GPIO_VALVE_2 }