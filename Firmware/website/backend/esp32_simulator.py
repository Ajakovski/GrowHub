import requests
import time
import random
import threading

API_URL = "http://localhost:8000/api/device/telemetry"
CAMERA_URL = "http://localhost:8000/api/device/camera"
HUB_ID = "hub_beta_001"
CAMERA_INDEX = 0
CAMERA_INTERVAL_SEC = 5
JPEG_QUALITY = 70

try:
    import cv2
except ImportError:
    cv2 = None

def generate_fake_telemetry():
    return {
        "hub_id": HUB_ID,
        "water_level_ok": random.choice([True, True, True, False]),
        "active_tiles": 2,
        "tiles": [
            {
                "tile_id": "tile_1",
                "moisture_level": round(random.uniform(30.0, 60.0), 1),
                "temperature": round(random.uniform(20.0, 25.0), 1),
            },
            {
                "tile_id": "tile_2",
                "moisture_level": round(random.uniform(25.0, 55.0), 1),
                "temperature": round(random.uniform(19.0, 24.0), 1),
            },
        ],
    }


def camera_loop():
    if cv2 is None:
        print("opencv-python not installed - camera feed disabled.")
        return

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"could not open webcam index {CAMERA_INDEX}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"webcam opened (index {CAMERA_INDEX}) - streaming to {CAMERA_URL}")
    consecutive_failures = 0

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            consecutive_failures += 1
            if consecutive_failures >= 5:
                print("webcam read failed repeatedly - retrying in 2s")
                time.sleep(2)
                consecutive_failures = 0
            continue

        consecutive_failures = 0
        ok, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
        )
        if not ok:
            continue

        try:
            response = requests.post(
                CAMERA_URL,
                files={"frame": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                timeout=10,
            )
            if response.status_code >= 400:
                print(f"camera upload failed: {response.status_code} {response.text[:120]}")
        except requests.exceptions.RequestException as error:
            print(f"camera upload error: {error}")

        time.sleep(CAMERA_INTERVAL_SEC)
                
        
print(f"Starting ESP32 simulator for {HUB_ID}...")
threading.Thread(target=camera_loop, daemon=True).start()

while True:
    payload = generate_fake_telemetry()
    try:
        response = requests.post(API_URL, json=payload)

        if response.status_code == 422:
            print("fastapi rejected the payload. error details:")
            print(response.text)
        else:
            print(
                f"sent data: moisture T1={payload['tiles'][0]['moisture_level']}% "
                f"| server says: {response.json().get('action')}"
            )
    except requests.exceptions.ConnectionError:
        print("Failed to connect to FastAPI. Is the server running?")

    time.sleep(5)
    