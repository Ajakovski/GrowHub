from skills.registry import skill

TARGET_RANGES = {
    "system": "Deep Water Culture (DWC) hydroponics with an 18 L shared reservoir",
    "water_temperature_c": {
        "ideal": [18, 22],
        "acceptable": [16, 24],
        "notes": "Measured in the hub's shared reservoir. Above 24 C dissolved oxygen drops and root rot "
        "risk rises; below 16 C growth slows. The hub's water heater switches on below about 20 C; "
        "it can only warm the water so high temperatures need cooling or shade. Cold water while "
        "the heater is on suggests a faulty or undersized heater.",
    },
    "ec_ms_cm": {
        "general": [0.8, 2.5],
        "by_crop": {
            "lettuce_and_leafy_greens": [0.8, 1.2],
            "herbs_such_as_basil": [1.0, 1.6],
            "strawberries": [1.0, 1.5],
            "peppers": [1.8, 2.8],
            "tomatoes": [2.0, 3.5],
        },
        "notes": "Low EC means nutrients are depleted (dose the reservoir); high EC means too concentrated "
                 "(top up with plain water). EC rising while the water level drops usually means plants "
                 "are drinking water faster than nutrients.",
    },
    "ph": {
        "ideal": [5.5, 6.5],
        "target_after_mixing": 5.8,
        "notes": "pH ussualy drifts upward as plants feed. Outside 5.5-6.5 some nutrients become "
                 "unavailable even when EC is fine. Correct with pH down or pH up in small doses.",
    },
    "air_temperature_c": {
        "ideal": [18, 27],
        "acceptable": [15, 30],
        "notes": "Measured under each tile's LED canopy, which runs a couple of degrees warmer than the room "
                 "while the lights are on. Above 30 C plants suffer heat stress."
    },
    "humidity_percent": {
        "ideal": [50, 70],
        "acceptable": [40, 80],
        "notes": "Measured per tile. Humidity rises as plants grow and transpire. Above 80% mould and "
                 "leaf disease risk rises (improve airflow); below 40% leaves can dry out.",
    },
    "water_flow_l_min": {
        "normal": [1.6, 2.4],
        "low_below": 1.0,
        "notes": "Measured per tile. Low flow in on tile points to a clog in that tiles piping, often "
                 "roots or debris. Low flow in every tile at once points to the pump or a reservoir that is "
                 "nearly empty.",
    },
    "light_lux": {
        "leds_on": [15000, 30000],
        "schedule": "LED canopy on 06:00-22:00 (16 hours) by default",
        "notes": "Readings near 0 while the LEDs should be on point to a failed canopy or sensor; "
                 "readings of a few hundred lux are ambient room light only.",
    },
    "reservoir": {
        "notes": "Top up when the level sensor reports low; change the full reservoir every 1-2 weeks.",
    },
}


@skill(
    "get_target_ranges",
    "Get the recommended ranges for water temperature, EC, pH air temperature, humidity, water flow and "
    "light in a GrowHub DWC system, including "
    "EC ranges for common crops. Use this before judging whether a reading is good or bad.",
)
def get_target_ranges():
    return TARGET_RANGES
