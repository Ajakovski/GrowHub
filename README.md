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
| X | MCU MODULE | ESP32-S3-WROOM-1 N16R8 | LCC-54 | 1 | X | X |
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
| X | High Current Protection | INA226AIDGSR | VSSOP-10P | X | X |
| X | Input Protection Controller | LTC4364IS-2#PBF | 16-SOIC | X | X |

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
- [ ] Schematic Layout Main PCB
- [ ] PCB Design Main PCB
- [ ] Schematic Layout Floor PCB
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

# Creators

### Ajakovski - Hardware and PCB Design

### soggy8 - 3D Design and Software
