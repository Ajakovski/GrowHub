<div align="center">

# GrowHub - Vertical Garden

<p>
  <img src="./Documentation/Full GrowHub Garden.png" width="40%" height="500">
  <img src="./Documentation/Transparent Chess Board.png" width="40%" height="450">
</p>

### _A highly efficient vertical plant growing garden with AI controlls for user-free handling experience._ 
  
</div>

---

# Overview

***GrowHub - Vertical Garden***

A sophisticated way of growing whatever kind of plant (only legal ones :}) from your living room, balcony, even your bedroom or wherever you want!

The idea of the project is to have a care-free environment where the user only monitors his plants from the website and we the developers are resposnible for making everything functional for healthy and low-cost plant growing.

It is a modular garden capable of supplying 1-3 floors of growing area split between 8 tiles per floor!!!

With a good team we managed to split the 4 main segments of this project accordingly which are: PCB and electrical construction, mechanical functioning of the project, server control, User-friendly and work-free experience for the customers.

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

*Some modules are dependant based on the amount of floors accounted in the project (1-3)

_Everything is calculated for the highest amount of floors - 3_

| Designator | Function | Part | Package | Qty | Price(USD) | Link |
|---|---|---|---|---|---|---|
| U6 | MCU MODULE | ESP32-S3-WROOM-1U N16R8 | LCC-54 | 1 | $6.90 | [Mouser](https://www.mouser.com/en/ProductDetail/Espressif-Systems/ESP32-S3-WROOM-1U-N16R8?qs=Li%252BoUPsLEns6V0Pr5KRJtw%3D%3D) |
| X | Server (if cloud exempted) | Raspberry Pi 5 | X | 1 | X | X |
| U8 | Surge Protection | LTC4364IS-2_PBF | SOIC-16 | 1 | $14.82 | | [Mouser](https://www.mouser.com/en/ProductDetail/Analog-Devices/LTC4364IS-2PBF?qs=hVkxg5c3xu9riE%252B4zWkG8g%3D%3D) | 
| U10 | 24V->5V Buck | LMR33630ADDA | HSOP-8-1EP | 1 | $3.67 | [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/LMR33630ADDA?qs=r5DSvlrkXmL3yj62Sna%2FpQ%3D%3D) |
| U11 | Power Monitor | INA226AIDGSR | TSSOP-10 | 1 | $2.95	| [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/INA226AIDGSR?qs=tQG3bEuiOZD4quG3egR36g%3D%3D) 
| X | Humidity + Temp sensor | SHT40 | DFN | 1 | X | X |
| X | Light Sensor | VEML7700-TT | SMD-4P | 1 | X | X |
| X | LED Strips | WS2811 24V | 60/m 67IP | 5m | X | X |
| X | Level Shifter | 74AHCT125D | SOIC127P600X175-14N | 1 | X | X |
| X | Load cell ADC | NAU7802SGI | 16-SOIC | 1 | X | X |
| X | Power Supply | 24V 8A DC | X | 1 | X | X |
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
- [X] PCB Design Main PCB
- [X] Schematic Layout Floor PCB
- [X] PCB Design Floor PCB
- [ ] Firmware
- [ ] AI training
- [ ] Cloud or Raspberry server Integration
- [X] Final BOM
- [X] Create a Zine (if needed)
- [ ] Final build
- [ ] Add more sensors
- [ ] Lower BOM costs

---

# Software

Everything lives under `Firmware/website`. Compose brings up **backend**, **AI**, **nginx frontend**, and an optional **simulator**.

### Stack

| Piece | Location | Notes |
|---|---|---|
| Frontend | `frontend/` | Static HTML/CSS/JS (landing, how-it-works, shop, demo, login, dashboard) |
| Nginx | `nginx.conf` | Serves the site on `:5000` and proxies `/api/` → backend (same-origin cookies) |
| Backend | `backend/` | FastAPI on `:8000` — auth, web dashboard APIs, device ingest, AI status/controls |
| AI | `ai/` | FastAPI on `:8001` — chat + reviews; talks to the backend with `GROWHUB_AI_KEY` |
| Database | SQLite | Accounts, sessions, hub history / plants / camera source / AI summaries |
| Simulator | `backend/esp32_simulator.py` | Fake hub telemetry + optional OpenCV webcam frames |

### Product surfaces

- **Landing** (`index.html`) — product story and contact
- **How it works** — AI care explainer + path into the demo
- **Catalog** (`shop.html`) — Hub / planter tile / stack modules from `/api/web/tiles`
- **Live demo** (`demo.html`) — `POST /api/auth/demo` guest session, then dashboard
- **Login / verify** — email + password; verification via Resend or backend log when unset
- **Dashboard** — plant stats, history (1h / 24h / 7d), camera (webcam or stock images), AI chat, plant picker  
  Guest sessions can **view** the shared hub but cannot change plants, camera source, or actuators via AI

### What the backend tracks

- Hub + per-tile telemetry: water temp / heater, EC, pH, reservoir level, air temp, humidity, light, flow
- Offline detection from report cadence (missed reports → hub offline UI)
- Sustained alerts (pH out of range, low/no flow, low water, cold water) — noisy single readings do not fire
- Actuator modes for lights / pump / heater (`auto` | `on` | `off`), returned to devices on the next telemetry cycle
- Camera frames in memory only (size-capped uploads); optional stock image folder for demos without a webcam
- Shared SQLite history (averaged charts, ~7 day retention)

### How to run (Docker, recommended)

From `Firmware/website`:

```bash
cp .env.example .env   # optional; fill LLM / email / secrets for a fuller setup
docker compose up -d --build
```

| URL | What |
|---|---|
| http://localhost:5000/ | Marketing site |
| http://localhost:5000/demo.html | Guest demo entry |
| http://localhost:5000/dashboard.html | Dashboard (login or demo) |
| http://localhost:8000/ | Backend API (direct; prefer `:5000/api/` from the browser) |
| http://localhost:8001/ | AI service |

```bash
docker compose down        # keep SQLite volume
docker compose down -v     # wipe growhub-data
```

The simulator mounts `/dev/video0`. Remove the `devices:` block in `compose.yaml` if you have no camera.

### How to run (manual)

1. Backend: from `Firmware/website/backend`, `uvicorn main:app --reload --port 8000`
2. Frontend: either nginx with `nginx.conf`, or temporarily `python -m http.server 5000` from `frontend/` (API calls should still hit the same origin or set `GROWHUB_API_ORIGIN`)
3. AI (optional): from `Firmware/website/ai`, run its uvicorn entry on `8001` with `GROWHUB_API_BASE` and keys set
4. Simulator: `python esp32_simulator.py` (needs `GROWHUB_DEVICE_KEY` matching the backend)

### Environment (high level)

Copy `Firmware/website/.env.example` → `.env`. Important knobs:

| Variable | Purpose |
|---|---|
| `GROWHUB_DEVICE_KEY` | Required for device ingest (unset → rejected unless `GROWHUB_ALLOW_INSECURE_DEVICE=1`) |
| `GROWHUB_AI_KEY` | Shared secret for AI ↔ backend status/controls and AI-key dashboard reads |
| `GROWHUB_TRUST_PROXY` | `1` in compose so rate limits use nginx `X-Real-IP` / `X-Forwarded-For` |
| `GROWHUB_COOKIE_SECURE` | `1` when serving HTTPS |
| `GROWHUB_WEB_ORIGIN_REGEX` | Allowed browser origins for cookies/CORS (default: localhost + LAN) |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | OpenAI-compatible provider for chat + reviews |
| `RESEND_API_KEY` / `GROWHUB_EMAIL_FROM` | Verification + contact email (empty → log verification links) |
| `GROWHUB_PUBLIC_URL` | Absolute base for verification links in production |

### Useful API routes

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` · `/login` · `/demo` · `/logout` | Accounts + guest demo |
| GET | `/api/auth/me` | Current user (`email`, `is_demo`) |
| GET | `/api/web/plant-stats` | Dashboard snapshot (auth or AI key) |
| GET | `/api/web/history?device=…&range=1h` | Chart history |
| PUT | `/api/web/plants` · `/camera-source` | Hub config (**non-demo users only**) |
| GET | `/api/web/camera` · `/camera/stream` | Still / MJPEG |
| POST | `/api/web/contact` | Contact form (honeypot + rate limit) |
| POST | `/api/device/telemetry` · `/camera` | Device ingest (`X-Device-Key`) |
| GET/PUT | `/api/ai/controls` | Actuator modes (`X-AI-Key`) |
| POST | AI `:8001/chat` · `/review` | Logged-in chat / on-demand review |

### Tests

From `Firmware/website/backend` (with `requirements-dev.txt` installed):

```bash
python -m pytest tests/ -q
```

Covers demo/auth, web API, security guards (demo read-only, device fail-closed, upload cap, proxy IP), and static frontend/nginx contracts.

### Deploy notes

For anything beyond local compose: use strong secrets (not the `dev-*-key` defaults), set `GROWHUB_COOKIE_SECURE=1` on HTTPS, prefer exposing only `:5000` (or your TLS terminator) rather than publishing `:8000` / `:8001`, and keep `GROWHUB_TRUST_PROXY` aligned with whether a reverse proxy sits in front of the backend.

### Status

The website/software part is done now. It features everything from the frontend all the way to the backend with AI, tests, docker compose files,
nginx conf files and everything. I think the hardware aka the PCB design is done as well so now we need to start working on the firmware.

---

# Creators

### Ajakovski - Hardware and PCB Design

### soggy8 - 3D Design and Software
