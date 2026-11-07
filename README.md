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
| U1 | USB-C Surge Protection | USBLC6-2P6 | SOT-666 | 1 | $0.69 | [Mouser](https://www.mouser.com/en/ProductDetail/STMicroelectronics/USBLC6-2P6?qs=6ARB0lp6jlViGcbUSvj1Mw%3D%3D) |
| U2 | Ambient Light Sensor | VEML7700-TT | XDCR_VEML7700-TT | 1 | $1.35 | [Mouser](https://www.mouser.com/en/ProductDetail/Vishay-Semiconductors/VEML7700-TT?qs=BcfjnG7NVaXdL6DJFdWbdw%3D%3D) |
| U3 | Load cell ADC | NAU7802SGI | SOIC-16 | 1 | $1.87 | [Mouser](https://www.mouser.com/en/ProductDetail/Nuvoton/NAU7802SGI?qs=A6eO%252BMLsxmSrxisJRahwRQ%3D%3D) |
| U4 | Valve Switch | TPS27S100BPWPR | HTSSOP-14 | 1 | $1.87 | [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TPS27S100BPWPR?qs=0lQeLiL1qyaF4011Zes0Yg%3D%3D) |
| U5,U7,U9 | I2C Buffers | PCA9600DPZ | TSSOP-8 | 3 | $21.00 | [Mouser](https://www.mouser.com/en/ProductDetail/NXP-Semiconductors/PCA9600DPZ?qs=Li%252BoUPsLEnu5vr2lXlgE1A%3D%3D)
| U8 | Surge Protection | LTC4364IS-2_PBF | SOIC-16 | 1 | $14.82 | | [Mouser](https://www.mouser.com/en/ProductDetail/Analog-Devices/LTC4364IS-2PBF?qs=hVkxg5c3xu9riE%252B4zWkG8g%3D%3D) | 
| U10 | 24V->5V Buck | LMR33630ADDA | HSOP-8-1EP | 1 | $3.67 | [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/LMR33630ADDA?qs=r5DSvlrkXmL3yj62Sna%2FpQ%3D%3D) |
| U11 | High Current Protection | INA226AIDGSR | TSSOP-10 | 1 | $2.95	| [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/INA226AIDGSR?qs=tQG3bEuiOZD4quG3egR36g%3D%3D) 
| U12 | I2C Mux | TCA9548APWR |  24-TSSOP | 1 | $1.65 | [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TCA9548APWR?qs=sGAEpiMZZMutXGli8Ay4kHAf4%2FN1WW693xDAZd3LyqA%3D) |
| C (various) | Decoupling / Bulk | 100nF, 1µF, 4.7µF, 10µF, 22µF | 0402/0603/0805/1206 | 105 | $16 | [Amazon](https://www.amazon.com/Bridgold-111Types-Capacitor-1pF-10uF-3-9pF-22uF/dp/B0C196FBK3/ref=sr_1_10?dib=eyJ2IjoiMSJ9.Sik-1N6T3B22pMHx3gZwssQe9HV9aXahGuDaX-uB1yfBLuMOqud5ObrWRTFUEP5qQT2cI_n6L6fgTxfF61UY6m7jwAR2JlYfwWtNi5UCKX4QVam3zu4P14UT01DyXCllphzxt5CmLBpMIcKJr-lpdFgCHgOWfw1AMDWRa0VJgoOHSTB1Ejcqxwg_bRNHyVE3csjNCQKdCS_s7IOfQRityBtC0y6ZoSuw4EYrFxCoT9w.R-0uFALOYO601m_UiLGERn05S21OQveJX7LUG-RrBD0&dib_tag=se&keywords=SMD%2BCapacitor&qid=1781345348&sr=8-10&th=1) |
| C (various) | Decoupling | 10nF | 0603 | 6 | $1.62 | [Mouser](https://www.mouser.com/en/ProductDetail/KEMET/C0603F103K8RACTU?qs=sGAEpiMZZMukHu%252BjC5l7YXqC3L5J1PSDOxyZlqyYeaQ%3D) |
| C11 | Decoupling | 330pF | 0603 | 1 | $0.20 | [Mouser](https://www.mouser.com/en/ProductDetail/Walsin/0603B331K100CT?qs=sGAEpiMZZMsh%252B1woXyUXj9Vc%2FsqQGnyV%2FOvNY0Ao%252BFA%3D) | 
| C(various) | Decoupling | 47nF | 0603 | 3 | $1.17 | [Mouser](https://www.mouser.com/en/ProductDetail/KEMET/C0603J473K8RAC7411?qs=sGAEpiMZZMukHu%252BjC5l7YXqC3L5J1PSDRSkJBnpGzwM%3D) |
| C19 | Decoupling | 1nF | 0603 | 1 | $0.19 | [Mouser](https://www.mouser.com/en/ProductDetail/KYOCERA-AVX/06031F102K4T2A?qs=%252BdQmOuGyFcFZxL9GWikwcQ%3D%3D) | 
| C(various) | Decouplong | 220nF | 0603 | 3 | $0.51 | [Mouser](https://www.mouser.com/en/ProductDetail/YAGEO/CC0603KPX7R6BB224?qs=57cj7OiSijk39MinEZxVnw%3D%3D) |
| C(various) | Bulk | 220uF | AEC | 7 | $18.41 | [Mouser](https://www.mouser.com/en/ProductDetail/Vishay-BC-Components/MAL215097102E3?qs=qmStTZH4TznNa7zgwdGJWg%3D%3D) |
| D(various) | Protective diode | ESD5Z3.3T1G | SOD-523-2 | 11 | $1.58 | [Mouser](https://www.mouser.com/en/ProductDetail/onsemi/ESD5Z3.3T1G?qs=OSf9jACorvaH3Y8oRWEcuQ%3D%3D) |
| D3 | Pump Diode | SS34 | DO-214AB | 1 | $1.01 | [Mouser](https://www.mouser.com/en/ProductDetail/onsemi/SS34?qs=2ONuHmP%2FXzb3ub11UdFfdQ%3D%3D) |
| D(various) | LED | SK6812 | 5050 | 3 | $2.95 | [Mouser](https://www.mouser.com/en/ProductDetail/Adafruit/4960?qs=pBJMDPsKWf1Q%252BqeEoLnQjA%3D%3D) |
| D(various) | Protective Diode | ESD5Z6.0T1G | SOD-523-2 | 10 | $0.9 | [Mouser](https://www.mouser.com/en/ProductDetail/onsemi/ESD5Z6.0T1G?qs=OSf9jACorvYUyIPFpvnErQ%3D%3D) |
| D(various) | Valve Diode | SS16 | DO-214AC-2 | 4 | $1.44 | [Mouser](https://www.mouser.com/en/ProductDetail/Taiwan-Semiconductor/SS16?qs=JV7lzlMm3yJVXqornbcQQA%3D%3D) |
| D21 | Filter Diode | 1N4148W | 	SOD-123F | 1 | $0.12 | [Mouser](https://www.mouser.com/en/ProductDetail/Diotec-Semiconductor/1N4148W?qs=OlC7AqGiEDmsbkbAeXQtXg%3D%3D) | 
| D23 | Filter Diode | SMBJ33A | DO-214AA | 1 | $0.77 | [Mouser](https://www.mouser.com/en/ProductDetail/Semtech/SMBJ33A?qs=jcD%2FCkGBYeN%2FjSJFT7pReg%3D%3D) |
| F1 | Little Fuse | 3A Slo-Blo 125V | X | 1 | $3.36 | [Mouser](https://www.mouser.com/en/ProductDetail/Littelfuse/0460003.UR?qs=YKoktUZms5J5DMRoJY1GHw%3D%3D) |
| IC1 | LED Signal optimiser | 74AHCT125D, 118 | SOIC-14 | 1 | $0.35 | [Mouser](https://www.mouser.com/en/ProductDetail/Nexperia/74AHCT125D118?qs=P62ublwmbi8WxHlonNNcrA%3D%3D) |
| J1 | USB-C port | USB-C 2495155-1 | X | 1 | $2.25	 | [Mouser](https://www.mouser.com/en/ProductDetail/TE-Connectivity/2495155-1?qs=2FehpBK1j95l8dIFdQH6Ww%3D%3D) |   
| J2 | Pump Conn | Micro-Fit 1x4 | X | 1 | $1.18 | [Mouser](https://www.mouser.com/en/ProductDetail/Molex/43650-0400?qs=A%252B%2FNCR0PvNV09lp6LzdRYg%3D%3D) |
| J4,J14,J15 | Floor Conn | Micro-Fit 3.0 2x6 | X | 3 | $9.24 | [Mouser](https://www.mouser.com/en/ProductDetail/Molex/43045-1213?qs=359VwiUTsp0cSsT%2FR1N%2Feg%3D%3D) |
| J5 | PSU DIN | KPJX-4S | 1 | $1.69 | [Mouser](https://www.mouser.com/en/ProductDetail/Kycon/KPJX-4S?qs=PGF6ObTbUZ1PHc9As62%2FZQ%3D%3D) |
| J8,J9,J10 | Valve Conn | G88MPB02002C1EU | X | 3 | $2.34 | [Mouser](https://www.mouser.com/en/ProductDetail/Amphenol-Commercial-Products/G88MPB02002C1EU?qs=%252BRAvXJslkuDOP%2FIlLZvKQA%3D%3D) |
| J11 | Load Cell Conn | JST PH 5p | X | 1 | $0.69 | [Mouser](https://www.mouser.com/en/ProductDetail/JST-Commercial/B5B-PH-K-S-GW?qs=cIziFXvMxOWNYlDdZstBdA%3D%3D) |
| J12 | Base Leak Conn | JST PH 2p | X | 1 | $0.19 | [Mouser](https://www.mouser.com/en/ProductDetail/JST-Commercial/B2B-PH-K-MLFSN?qs=QpmGXVUTftFtjXkolasBkg%3D%3D) |
| J13 | Float S11 | JST PH 2p | X | 1 | $0.19 | [Mouser](https://www.mouser.com/en/ProductDetail/JST-Commercial/B2B-PH-K-MLFSN?qs=QpmGXVUTftFtjXkolasBkg%3D%3D) |
| L1 | Voltage Regulation | 8.2uH | 1 | $5.11 | [Mouser](https://www.mouser.com/en/ProductDetail/Coilcraft/XAL1010-822MED?qs=zCSbvcPd3pba7AVSEX0Sqw%3D%3D) |
| L2 | Voltage Regulation | 6.8uH | 1 | $3.06 | [Mouser](https://www.mouser.com/en/ProductDetail/Coilcraft/XAL7070-682MEC?qs=zCSbvcPd3pZMktES6ULAbA%3D%3D) |
| PS1 | 5V->3.3V Regulator | LMR33610ADDAR | HSOP-8 | 1 | $2.39 | [Mouser](https://www.mouser.com/en/ProductDetail/Texas-Instruments/LMR33610ADDAR?qs=Cb2nCFKsA8qZzeebnoCDFA%3D%3D) |
| Q1-Q9 | Driver FETs | BSS138BK-215 | TO-236AB-3 | 10 | $1.15 | [Mouser](https://www.mouser.com/en/ProductDetail/Nexperia/BSS138BK215?qs=A1cBxND5mHIu7uZeHkM5Xw%3D%3D) |



*Notice: These shipping costs are for a Balkan country so if youa re from EU or USA there are very high chances of having lower shipping costs*

*Notice: These are just recommendations that i have found to be secure and hopefully the cheapest possible option available. Do your onw research if you think that better deals exist on the current market depending on when you are buing it*.

---

# Features 

- **High Efficiency** - Greater production compared to normal gardening
- **Water Saving** - Lower consumption through optimised watering systems
- **Small occupation of space** - The vertical trait makes it suitable for homes
- **Care-Free Product** - Everything is automated
- **User friendly** - No need of gardening expertise to start

---

# PCB Design

The PCB was designed specifically for this project and its layout.

Key concepts of the design:
- 4 layer on main PCB
- Work is split on two PCBs
- GND Plane on L2 for return path
- GND Fill on L1,L3,L4 for signal integrity
- Power Fills for certain areas of L3
- Protection circuits and components for safety

## PCB Layout

### Main PCB

_*Some pictures may have been distorted in order to fit them in the README.*

<img src="./Documentation/Pictures/Journal_AJ/Image.png" width="80%" height="80%">

### Floor PCB

<img src="./Documentation/Pictures/Floor_PCB.png" width="100%" height="100%">

---
 
## Schematic

***Refer to the PDF file for better overview*** [PDF](Documentation/GrowHub_Elec.pdf)

### Main Schematic

#### Main Floor Schematic

<img src="./Documentation/Pictures/Main_Sch.png">

#### Board IO Schematic

<img src="./Documentation/Pictures/Board_IO_Sch.png">

### Floor Schematic

<img src="./Documentation/Pictures/Floor_Sch.png">

## Components Placement

<div align="center">

### Main PCB

<img src="./Documentation/Pictures/Main_PCB.png">

### Floor PCB

<img src="./Documentation/Pictures/Journal_AJ/Image68.png">

</div>

---

# Assembly Guide

## Hardware

***A visual representation of the whole project has been provided withing repository files***

```
Hardware/FULLY_ASSEMBLED_PROJECT.step
```

### 1. Order the PCBs and 3D Model

Navigate to: (For PCBs)

```bash
Hardware/KiCad/Gerbers/
```

Some files are in zip files due to github memory restrictions.

*Upload the G-Code files to your preferred manufacturer and order the parts.*

### 2. Order the Components

Whether you want to order it trough PCBA or solder it manually you should refer to the BOM file.

```bash
Hardware/BOM.csv
```

I recommend getting PCBA or sorting them out before you start assembling because this is a big project with loads of components.

### 3. Soldering Process

I highly suggest using oven reflow or hot pad soldering for the SMD whether you have decided to assemble it yourself.

Solder in regions if you use a smaller heating plate and always double check how you place the components.

Place larger modules first and then every passive peripheral components.

Some soldering might require a soldering iron due to L1 fill and heat dissipation in the copper.

Recommended tools are:
- FLux
- Reflow soldering oven or Heating plate for soldering
- Tweezers for placing the components
- Solder paste
- Helping hands with a magnifying glass would be wonderfull

### 4. Assemble the PCBs in the Enclosure

***Materials needed for assembling:***

- 16x m3 Screw nuts (if you install main board +3 floor boards)
- Other screws should come with the designated components.

***Steps for assembling***



---

# Software

Everything lives under `Software/website`. Compose brings up **backend**, **AI**, **nginx frontend**, and an optional **simulator**.

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

From `Software/website`:

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

1. Backend: from `Software/website/backend`, `uvicorn main:app --reload --port 8000`
2. Frontend: either nginx with `nginx.conf`, or temporarily `python -m http.server 5000` from `frontend/` (API calls should still hit the same origin or set `GROWHUB_API_ORIGIN`)
3. AI (optional): from `Software/website/ai`, run its uvicorn entry on `8001` with `GROWHUB_API_BASE` and keys set
4. Simulator: `python esp32_simulator.py` (needs `GROWHUB_DEVICE_KEY` matching the backend)

### Environment (high level)

Copy `Software/website/.env.example` → `.env`. Important knobs:

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

From `Software/website/backend` (with `requirements-dev.txt` installed):

```bash
python -m pytest tests/ -q
```

Covers demo/auth, web API, security guards (demo read-only, device fail-closed, upload cap, proxy IP), and static frontend/nginx contracts.

### Deploy notes

For anything beyond local compose: use strong secrets (not the `dev-*-key` defaults), set `GROWHUB_COOKIE_SECURE=1` on HTTPS, prefer exposing only `:5000` (or your TLS terminator) rather than publishing `:8000` / `:8001`, and keep `GROWHUB_TRUST_PROXY` aligned with whether a reverse proxy sits in front of the backend.

---

# Current Status

- [X] Initial Concept
- [X] Component List
- [X] Schematic Layout Main PCB
- [X] PCB Design Main PCB
- [X] Schematic Layout Floor PCB
- [X] PCB Design Floor PCB
- [ ] Firmware
- [X] Software
- [X] Final BOM
- [X] Create a Zine (if needed)
- [X] Final build
- [ ] Add more sensors
- [ ] Lower BOM costs

---

# Creators

### Ajakovski - Hardware and PCB Design

### soggy8 - 3D Design and Software
