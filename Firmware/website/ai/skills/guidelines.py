from skills.registry import skill

TARGET_RANGES = {
    "system": "Deep Water Culture (DWC) hydroponics with an 18 L shared reservoir",
    "water_temperature_c": {
        "ideal": [18, 22],
        "acceptable": [16, 24],
        "notes": "Above 24 C dissolved oxygen drops and root rot risk rises; below 16 C growth slows.",
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
        "notes": "GrowHub has no pH sensor yet; suggest a manual check if nutrient problems persist "
                 "while EC is in range.",
    },
    "reservoir": {
        "notes": "Top up when the level sensor reports low; change the full reservoir every 1-2 weeks.",
    },
}


@skill(
    "get_target_ranges",
    "Get the recommended ranges for water temperature, EC and pH in a GrowHub DWC system, including "
    "EC ranges for common crops. Use this before judging whether a reading is good or bad.",
)
def get_target_ranges():
    return TARGET_RANGES
