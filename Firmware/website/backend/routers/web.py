from fastapi import APIRouter

router = APIRouter()

@router.get("/tiles")
async def get_hardware_catalog():
    return [
        {
            "id": "module_15x15",
            "name": "15x15 Hydroponic Base Tile",
            "category": "modules",
            "price": 39.99
        },
        {
            "id": "hub_ai",
            "name": "Central Control Hub",
            "category": "tech",
            "price": 59.99
        }
    ]

@router.get("/plant-stats")
async def get_plant_stress():
    return {
        "plant_name": "Basil - Tile #1",
        "moisture_level": 50,
        "temperature": 22.5,
        "water_level_ok": True,
        "ai_health_score": 85,
        "camera_feed_url": "https://www.google.com"
    }