<div align="center">

# GrowHub - Vertical Garden

<p>
  <!--Pictures will be placed here in the future-->
</p>

### _A highly efficient vertical plant growing garden with AI controlls for user-free handling experience._ 
  
</div>

---

# Overview

***WARNING!!!***
_This is a README created in particular only for week 1 on Thirdspace so that we can ship the project. Future README versions will be far more advanced._

***GrowHub - Vertical Garden***

A sophisticated way of growing whatever kind of plant (only legal ones :}) from your living room, balcony, even your bedroom or wherever you want!

The idea of the project is to have a work-free environment where the user only monitors his plants from the website and we the developers are resposnible for making everything functional for healthy and low-cost plant growing.

It is a modular garden capable of supplying 1-3 floors of growing area split between 8 tiles per floor!!!

With a good team we managed to split the 4 main segments of this project accordingly which are: PCB and electrical construction, mechanical functioning of the project, AI and server control, User-friendly and work-free experience for the customers.

---

# Motivation

In todays world a lot more people are living in flats and with the constant inflation plus the enforcment of consuming lab products a lot of people are getting restrained of consuming real, healthy and natural food.

The soil is constantly polluted due to new construction working and the constant droughts are limiting the farmers to produce enough single-ingredient food for the families in the metropolitan cities.

With those issues on mind me and my friend have come up with an idea to revolutionize the way people are getting natural ingreidents in their households.

The main goals that we want to achieve are the following:

- User-friendly and work-free experience for anyone having this product
- Highly efficiency for growing plants
- Healthy environment for both the plants and users

A lot of working skills are required for this project to succeed so i hope you understand our issues with shipping functional projects in Week 1.

---

# BOM

**BOM.csv is still not present due to unfinished secondary PCBs**

*Some modules are dependant based on the amount of floors accounted in the project (1-3)

| Designator | Function | Part | Package | Qty | Price(USD) | Link |
|---|---|---|---|---|---|---|
| X | MCU MODULE | ESP32-S3-WROOM-1U N16R8 | LCC-54 | 1 | X | X |
| X | Server (if cloud exempted) | Raspberry Pi 5 | X | 1 | X | X |
| X | Soil moisture sensor | Capactive | X | 8-24 | X | X |
| X | CO2 Sensor | SC41-D-R2 NDIR | X | 1 | X | X | 
| X | Humidity + Temp sensor | SHT40 | DFN | 1 | X | X |
| X | Light Sensor | VEML7700-TT | SMD-4P | 1 | X | X |
| X | LED Strips | WS2811 24V | 60/m 67IP | 5m | X | X |
| X | Level Shifter | 74AHCT125D | SOIC127P600X175-14N | 1 | X | X |
| X | Load cell ADC | NAU7802SGI | 16-SOIC | 1 | X | X |
| X | Power Supply | 24V 8A DC | X | 1 | X | X |
| X | 24V->5V Buck | LMR33630ADDA | HSOIC | 1 | X | X |
| X | 5V->3V3 Buck | LMR33610BDDAR | HSOIC | 1 | X | X |
| X | High Current Protection | INA226AIDGSR | VSSOP-10P | 1 | X | X |
| X | Input Protection Controller | LTC4364IS-2#PBF | 16-SOIC | 1 | X | X |
| X | I2C Mux | TCA9548APWR |  24-TSSOP | 4 | X | X |
| X | Analog Mux | ADG706BRU | RU-28 | 3 | X | X |
| X | I/O Expander | MCP23017T | SOIC-28 | 3 | X | X |
| X | ADC 16-bit | ADS1115IDGSR | DGS | 3 | X | X |
| X | PWM Expander | PCA9685BS_118 | 28-HVQFN | 3 | X | X |
| X | I2C Buffer | P82B96D | SOIC-8 | 3 | X | X |
| X | Board ID | DS28E07Q_T | TDFN-EP | 3 | X | X |

*Notice: These shipping costs are for a Balkan country so if youa re from EU or USA there are very high chances of having lower shipping costs*

*Notice: These are just recommendations that i have found to be secure and hopefully the cheapest possible option available. Do your onw research if you think that better deals exist on the current market depending on when you are buing it*.

---

# Planned Features 

- High production %
- Lower water waste
- Small occupacy of space
- Automated garden control
- User friendly and work-free 

---

# Current Status

- [X] Initial Concept
- [X] Component List
- [X] Schematic Layout Main PCB
- [ ] PCB Design Main PCB
- [X] Schematic Layout Floor PCB
- [ ] PCB Design Floor PCB
- [ ] Firmware
- [ ] AI training
- [ ] Cloud or Raspberry server Integration
- [ ] Final BOM
- [ ] Create a Zine (if needed)
- [ ] Final build
- [ ] Add more sensors
- [ ] Lower BOM costs

---

# Software

The software side of GrowHub is the live monitoring layer: a local FastAPI backend, a web dashboard, and an ESP32-style simulator that can also push webcam frames so the optical node on the dashboard feels real during development.

### Stack

- **Frontend** — static site under `Firmware/website/frontend` (HTML / CSS / JS)
- **Backend** — FastAPI app under `Firmware/website/backend` (`uvicorn`, port `8000`)
- **Database** — SQLite (`growhub.db`) for sensor history, no extra server needed
- **Simulator** — `esp32_simulator.py` (fake hub telemetry + optional webcam upload via OpenCV)
- **Docker Compose** — `Firmware/website/compose.yaml` starts all three with one command

### What it does today

- Hub + per-tile telemetry (moisture, temperature, water reservoir, AI status)
- Device selector to switch between **Main Hub** averages and individual tiles
- Live “last updated” stamp and 1-hour sparklines on the moisture / temperature cards
- Sensor history stored on the backend in SQLite, so every browser sees the same charts and they survive refreshes and restarts
- Expandable moisture / temperature cards with a larger history chart (min / avg / max) and **1h / 24h / 7d** range buttons
- History is averaged into at most 120 points per chart and kept for **7 days**, older readings are deleted automatically
- **Hub offline detection**: the backend tracks when the hub last reported and how often it reports. If about 3 reports are missed (never less than 30 seconds), the dashboard shows a red "Hub offline" pill, "Last report Xm ago", and fades the last known values. This works for both the 5-second simulator and a real ESP32 that wakes every 15 minutes
- **Alerts**: a red banner appears above the cards, and a red dot on that device's button, when a tile stays below 30% moisture or the reservoir stays low for 3 readings in a row. One noisy reading never triggers an alert
- Camera still feed served by the backend (`/api/web/camera`) and shown on the dashboard. Frames are kept in memory only, never written to the database
- Simulator posts JSON telemetry to `/api/device/telemetry` and JPEG frames to `/api/device/camera` every 5 seconds

### How to run (Docker, recommended)

From `Firmware/website`:

```bash
docker compose up -d --build
```

- Dashboard: `http://localhost:5000/dashboard.html`
- API: `http://localhost:8000`
- Stop everything with `docker compose down` (history stays in the `growhub-data` volume; `docker compose down -v` wipes it)
- The simulator container uses the webcam at `/dev/video0`. Remove the `devices` lines in `compose.yaml` if your machine has no camera

### How to run (manually, three terminals)

1. Start the API from `Firmware/website/backend` (example: `uvicorn main:app --reload --port 8000`)
2. Serve the frontend (example: `python -m http.server 5000` from `Firmware/website/frontend`)
3. Run the simulator: `python esp32_simulator.py`
4. Open the dashboard and hard-refresh if assets were just updated

Optional environment variables:

| Variable | Default | Used by |
|---|---|---|
| `GROWHUB_DB_PATH` | `backend/growhub.db` | Backend, where the SQLite file lives |
| `GROWHUB_API_BASE` | `http://localhost:8000` | Simulator, which backend to post to |
| `CAMERA_INDEX` | `0` | Simulator, which webcam OpenCV opens |

Useful endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/web/plant-stats` | Current hub/tile state for the dashboard, plus `hub_online`, `last_telemetry_at` and active `alerts` |
| GET | `/api/web/history?device=hub&range=1h` | Moisture / temperature history (`device` = `hub` or a tile id, `range` = `1h`, `24h`, `7d`) |
| POST | `/api/device/telemetry` | Simulator / device telemetry ingest |
| POST | `/api/device/camera` | Upload latest camera frame |
| GET | `/api/web/camera` | Latest still image for the dashboard |

### Status

Software is further ahead than the physical build: the dashboard and simulator loop are usable now, while schematic / PCB / final sensor wiring are still in progress on the hardware side.

---

# Creators

### Ajakovski - Hardware and PCB Design

### soggy8 - 3D Design and Software
