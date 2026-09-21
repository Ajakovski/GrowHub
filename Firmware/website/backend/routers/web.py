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