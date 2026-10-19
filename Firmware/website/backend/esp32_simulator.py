import math
import os
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import requests

API_BASE = os.environ.get("GROWHUB_API_BASE", "http://localhost:8000")
API_URL = f"{API_BASE}/api/device/telemetry"
CAMERA_URL = f"{API_BASE}/api/device/camera"
HUB_ID = os.environ.get("GROWHUB_HUB_ID", "hub_beta_001")
DEVICE_KEY = os.environ.get("GROWHUB_DEVICE_KEY")
HEADERS = {"X-Device-Key": DEVICE_KEY} if DEVICE_KEY else {}
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
CAMERA_INTERVAL_SEC = 5
JPEG_QUALITY = 70

REPORT_INTERVAL_SEC = float(os.environ.get("SIM_REPORT_INTERVAL_SEC", "5"))
SIM_SPEED = float(os.environ.get("SIM_SPEED", "60"))
SIM_TILES = int(os.environ.get("SIM_TILES", "2"))
SIM_SEED = os.environ.get("SIM_SEED")

RESERVOIR_LITRES = 18.0
LOW_WATER_LITRES = 5.0
PUMP_STARVED_LITRES = 1.8
PUMP_FULL_FLOW_LITRES = 2.8
ROOT_REACH_LITRES = 1.5
TARGET_EC = 1.6
NUTRIENT_TO_WATER_UPTAKE = 0.75
TARGET_PH = 5.8
PH_RISE_PER_LITRE = 0.04
PH_CORRECT_ABOVE = 6.4
GROWER_DELAY_HOURS = (2.0, 14.0)
RESERVOIR_CHANGE_DAYS = 7.0

LIGHTS_ON_HOUR = 6
LIGHTS_OFF_HOUR = 22
LED_LUX = (17000.0, 22000.0)
LED_CANOPY_HEAT_C = 2.0
SUNRISE_HOUR = 7
SUNSET_HOUR = 19
DAYLIGHT_PEAK_LUX = 600.0

HEATER_SETPOINT_C = 20.0
HEATER_HYSTERESIS_C = 0.3
HEATER_C_PER_HOUR = 2.0

ROOM_HUMIDITY = 55.0
TRANSPIRATION_HUMIDITY = 10.0
HUMIDITY_TAU_HOURS = 0.5

NOMINAL_FLOW_LPM = (1.8, 2.2)
LOW_FLOW_LPM = 1.0
CLOGS_PER_TILE_PER_DAY = 0.1
CLOG_GROWTH_PER_HOUR = (0.03, 0.08)
MAX_CLOG = 0.9

DAILY_UPTAKE_LITRES = 2.5
MAX_GROWTH = 2.0
GROWTH_PER_DAY = 0.04

WATER_TEMP_TAU_HOURS = 3.0
WEATHER_TAU_HOURS = 12.0
WEATHER_SIGMA = 1.0

try:
    import cv2
except ImportError:
    cv2 = None


def _approach(current: float, target: float, hours: float, tau_hours: float) -> float:
    return current + (target - current) * (1 - math.exp(-hours / tau_hours))


@dataclass
class Tile:
    tile_id: str
    vigour: float
    air_offset: float
    led_lux: float
    nominal_flow: float
    humidity: float = ROOM_HUMIDITY
    growth: float = 1.0
    clog: float = 0.0
    clog_rate: float = 0.0
    low_flow_since: Optional[datetime] = None
    unclog_delay: float = 0.0

    def uptake_litres(self, hours: float, air_temp: float, lights_on: bool) -> float:
        demand = 1.0 + 0.06 * (air_temp - 20.0)
        if not lights_on:
            demand *= 0.3
        return max(0.0, DAILY_UPTAKE_LITRES / 24.0 * hours * self.growth * self.vigour * demand)


class Greenhouse:
    def __init__(self, start: datetime, tile_count: int, rng: random.Random):
        self.rng = rng
        self.clock = start
        self.weather = 0.0
        self.volume = RESERVOIR_LITRES
        self.nutrients = RESERVOIR_LITRES * TARGET_EC
        self.ph = TARGET_PH
        self.heater_on = False
        self.low_since = None
        self.refill_delay = self._grower_delay()
        self.ph_high_since = None
        self.ph_delay = self._grower_delay()
        self.last_change = start
        self.tiles = [
            Tile(
                tile_id=f"tile_{index + 1}",
                vigour=rng.uniform(0.85, 1.1),
                air_offset=rng.uniform(-0.5, 0.8),
                led_lux=rng.uniform(*LED_LUX),
                nominal_flow=rng.uniform(*NOMINAL_FLOW_LPM),
            )
            for index in range(tile_count)
        ]
        self.water_temp = max(self._passive_water_temp(), HEATER_SETPOINT_C)
        for tile in self.tiles:
            tile.humidity = self._humidity_target(tile)

    def _grower_delay(self) -> float:
        return self.rng.uniform(*GROWER_DELAY_HOURS)

    @property
    def hour(self) -> float:
        return self.clock.hour + self.clock.minute / 60

    @property
    def lights_on(self) -> bool:
        return LIGHTS_ON_HOUR <= self.clock.hour < LIGHTS_OFF_HOUR

    @property
    def ec(self) -> float:
        return self.nutrients / self.volume

    @property
    def pump_output(self) -> float:
        span = PUMP_FULL_FLOW_LITRES - PUMP_STARVED_LITRES
        return min(1.0, max(0.0, (self.volume - PUMP_STARVED_LITRES) / span))

    def room_temp(self) -> float:
        daily = 21.0 + 3.0 * math.sin(2 * math.pi * (self.hour - 9) / 24)
        return daily + self.weather + (1.0 if self.lights_on else 0.0)

    def tile_air_temp(self, tile: Tile) -> float:
        return self.room_temp() + tile.air_offset + (LED_CANOPY_HEAT_C if self.lights_on else 0.0)

    def _passive_water_temp(self) -> float:
        return self.room_temp() - 0.5 + (0.8 if self.lights_on else 0.0)

    def _humidity_target(self, tile: Tile) -> float:
        room = ROOM_HUMIDITY - 1.5 * (self.room_temp() - 21.0)
        transpiration = TRANSPIRATION_HUMIDITY * tile.growth * tile.vigour * (1.0 if self.lights_on else 0.5)
        canopy_warming = 2.5 * (self.tile_air_temp(tile) - self.room_temp())
        return min(98.0, max(25.0, room + transpiration - canopy_warming))

    def daylight_lux(self) -> float:
        if not SUNRISE_HOUR <= self.hour < SUNSET_HOUR:
            return 0.0
        return DAYLIGHT_PEAK_LUX * math.sin(math.pi * (self.hour - SUNRISE_HOUR) / (SUNSET_HOUR - SUNRISE_HOUR))

    def tile_flow(self, tile: Tile) -> float:
        return tile.nominal_flow * (1 - tile.clog) * self.pump_output

    def step(self, hours: float) -> None:
        if hours <= 0:
            return
        self.clock += timedelta(hours=hours)

        decay = math.exp(-hours / WEATHER_TAU_HOURS)
        self.weather = self.weather * decay + self.rng.gauss(0, WEATHER_SIGMA * math.sqrt(1 - decay ** 2))

        self._update_water_temp(hours)

        for tile in self.tiles:
            air = self.tile_air_temp(tile)
            drunk = min(tile.uptake_litres(hours, air, self.lights_on), max(0.0, self.volume - ROOT_REACH_LITRES))
            self.nutrients -= drunk * self.ec * NUTRIENT_TO_WATER_UPTAKE
            self.volume -= drunk
            self.ph += drunk * PH_RISE_PER_LITRE
            tile.growth = min(MAX_GROWTH, tile.growth + GROWTH_PER_DAY * hours / 24 * tile.vigour)
            tile.humidity = _approach(tile.humidity, self._humidity_target(tile), hours, HUMIDITY_TAU_HOURS)
            self._update_clog(tile, hours)

        self._maintain_reservoir()

    def _update_water_temp(self, hours: float) -> None:
        self.water_temp = _approach(self.water_temp, self._passive_water_temp(), hours, WATER_TEMP_TAU_HOURS)
        if self.heater_on:
            self.water_temp += HEATER_C_PER_HOUR * hours

        if self.water_temp < HEATER_SETPOINT_C - HEATER_HYSTERESIS_C:
            self.heater_on = True
        elif self.water_temp > HEATER_SETPOINT_C + HEATER_HYSTERESIS_C:
            self.heater_on = False

    def _update_clog(self, tile: Tile, hours: float) -> None:
        if tile.clog_rate == 0.0 and self.rng.random() < 1 - math.exp(-CLOGS_PER_TILE_PER_DAY * hours / 24):
            tile.clog_rate = self.rng.uniform(*CLOG_GROWTH_PER_HOUR)
            print(f"[{self.clock:%a %H:%M}] {tile.tile_id}: roots and debris starting to clog the piping")
        tile.clog = min(MAX_CLOG, tile.clog + tile.clog_rate * hours)

        if tile.clog == 0.0 or self.tile_flow(tile) >= LOW_FLOW_LPM:
            tile.low_flow_since = None
        elif tile.low_flow_since is None:
            tile.low_flow_since = self.clock
            tile.unclog_delay = self._grower_delay()
        elif self.clock - tile.low_flow_since >= timedelta(hours=tile.unclog_delay):
            print(f"[{self.clock:%a %H:%M}] {tile.tile_id}: piping cleared, flow restored")
            tile.clog = tile.clog_rate = 0.0
            tile.low_flow_since = None

    def _maintain_reservoir(self) -> None:
        if self.clock - self.last_change >= timedelta(days=RESERVOIR_CHANGE_DAYS):
            self.volume = RESERVOIR_LITRES
            self.nutrients = RESERVOIR_LITRES * TARGET_EC
            self.ph = TARGET_PH
            self.last_change = self.clock
            self.low_since = self.ph_high_since = None
            print(f"[{self.clock:%a %H:%M}] weekly reservoir change: fresh {RESERVOIR_LITRES:.0f} L "
                  f"at EC {TARGET_EC}, pH {TARGET_PH}")
            return

        if self.volume >= LOW_WATER_LITRES:
            self.low_since = None
        elif self.low_since is None:
            self.low_since = self.clock
        elif self.clock - self.low_since >= timedelta(hours=self.refill_delay):
            added = RESERVOIR_LITRES - self.volume
            self.nutrients += added * TARGET_EC
            self.ph = (self.ph * self.volume + TARGET_PH * added) / RESERVOIR_LITRES
            self.volume = RESERVOIR_LITRES
            self.low_since = None
            self.refill_delay = self._grower_delay()
            print(f"[{self.clock:%a %H:%M}] reservoir topped up with {added:.1f} L, "
                  f"EC now {self.ec:.2f}, pH {self.ph:.2f}")

        if self.ph <= PH_CORRECT_ABOVE:
            self.ph_high_since = None
        elif self.ph_high_since is None:
            self.ph_high_since = self.clock
        elif self.clock - self.ph_high_since >= timedelta(hours=self.ph_delay):
            print(f"[{self.clock:%a %H:%M}] pH down dosed: {self.ph:.2f} -> {TARGET_PH}")
            self.ph = TARGET_PH
            self.ph_high_since = None
            self.ph_delay = self._grower_delay()

    def telemetry(self) -> dict:
        noise = self.rng.gauss
        daylight = self.daylight_lux()
        return {
            "hub_id": HUB_ID,
            "water_level_ok": self.volume >= LOW_WATER_LITRES,
            "water_temperature": round(self.water_temp + noise(0, 0.05), 1),
            "heater_on": self.heater_on,
            "ec_level": round(max(0.0, self.ec + noise(0, 0.02)), 2),
            "ph": round(self.ph + noise(0, 0.02), 2),
            "active_tiles": len(self.tiles),
            "tiles": [
                {
                    "tile_id": tile.tile_id,
                    "air_temperature": round(self.tile_air_temp(tile) + noise(0, 0.15), 1),
                    "humidity": round(min(100.0, max(0.0, tile.humidity + noise(0, 1.0))), 1),
                    "light_lux": round(max(0.0, ((tile.led_lux if self.lights_on else 0.0) + daylight)
                                           * (1 + noise(0, 0.015)))),
                    "flow_lpm": round(max(0.0, self.tile_flow(tile) + noise(0, 0.04)), 2),
                }
                for tile in self.tiles
            ],
        }


def camera_loop():
    if cv2 is None:
        print("opencv-python not installed — camera feed disabled. Run: pip install opencv-python-headless")
        return

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"could not open webcam index {CAMERA_INDEX} — camera feed disabled")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"webcam opened (index {CAMERA_INDEX}) — streaming to {CAMERA_URL}")
    consecutive_failures = 0

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            consecutive_failures += 1
            if consecutive_failures >= 5:
                print("webcam read failed repeatedly — retrying in 2s")
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
                headers=HEADERS,
                data={"hub_id": HUB_ID},
                files={"frame": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                timeout=10,
            )
            if response.status_code >= 400:
                print(f"camera upload failed: {response.status_code} {response.text[:120]}")
        except requests.exceptions.RequestException as error:
            print(f"camera upload error: {error}")

        time.sleep(CAMERA_INTERVAL_SEC)


def main():
    rng = random.Random(SIM_SEED)
    greenhouse = Greenhouse(datetime.now(), SIM_TILES, rng)
    print(f"Starting ESP32 simulator for {HUB_ID} at {SIM_SPEED:g}x speed with {SIM_TILES} tiles...")
    threading.Thread(target=camera_loop, daemon=True).start()

    last_tick = time.monotonic()
    while True:
        now = time.monotonic()
        greenhouse.step((now - last_tick) * SIM_SPEED / 3600)
        last_tick = now

        payload = greenhouse.telemetry()
        try:
            response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=10)

            if response.status_code == 401:
                print("server rejected the device key. Set GROWHUB_DEVICE_KEY to match the backend.")
            elif response.status_code == 422:
                print("fastapi rejected the payload. error details:")
                print(response.text)
            else:
                flows = " ".join(f"{tile['flow_lpm']:.1f}" for tile in payload["tiles"])
                print(
                    f"[{greenhouse.clock:%a %H:%M}] lights {'on ' if greenhouse.lights_on else 'off'} "
                    f"| reservoir {greenhouse.volume:4.1f} L | water {payload['water_temperature']}°C "
                    f"heater {'on ' if greenhouse.heater_on else 'off'} | EC {payload['ec_level']:.2f} "
                    f"| pH {payload['ph']:.2f} | flow L/min {flows}"
                )
        except requests.exceptions.RequestException as error:
            print(f"Failed to reach FastAPI ({error.__class__.__name__}). Is the server running?")

        time.sleep(REPORT_INTERVAL_SEC)


if __name__ == "__main__":
    main()
