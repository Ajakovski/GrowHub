import requests
import time
import random

API_URL = "http://localhost:8000/api/device/telemetry"
HUB_ID = "hub_beta_001"

def generate_fake_telemetry():
    return {
        "hub_id": HUB_ID,
        "water_level_ok": random.random() < 0.75,
        "active_tiles": 2,
        "tiles": [
            {
                "tile_id": "tile_1",
                "moisture_level": round(random.uniform(30.0, 60.0), 1),
                "temperature": round(random.uniform(20.0, 25.0), 1)
            },
            {
                "tile_id": "tile_2",
                "moisture_level": round(random.uniform(25.0, 55.0), 1),
                "temperature": round(random.uniform(19.0, 24.0), 1)
            }
        ]
    }

print(f"Starting ESP32 simulator for {HUB_ID}...")

while True:
    payload = generate_fake_telemetry()
    try:
        response = requests.post(API_URL, json=payload)

        if response.status_code == 422:
            print("fastapi rejected the payload. error details:")
            print(response.text)
        else:
            print(f"sent data: moisture T1={payload['tiles'][0]['moisture_level']}% | server says: {response.json().get('action')}")
    except requests.exceptions.ConnectionError:
        print(f"Failed to connect to FastAPI. Is the server running?")

    time.sleep(5)            