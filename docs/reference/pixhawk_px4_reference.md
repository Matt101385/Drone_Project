# Pixhawk / PX4 Reference

## Current Role

Pixhawk 6X is the flight controller. PX4 runs the flight-control stack. The Raspberry Pi 5 sends MAVLink/MAVSDK commands through the Pixhawk TELEM2 serial port.

## Confirmed Hardware

| Field | Value |
| --- | --- |
| Aircraft platform | Holybro X500 V2 quadcopter |
| Wheelbase | 500 mm |
| Frame weight | 610 g |
| Frame body | 144 x 144 mm, 2 mm thick |
| Landing gear height | 215 mm |
| Flight controller | Pixhawk 6X |
| Firmware stack | PX4 |
| GPS module | Holybro M10 GPS module |
| Battery type | 4S LiPo, XT60 |
| Recommended battery | 4S 3000-5000 mAh, 20C+ LiPo |
| Motors | Holybro 2216 KV920 motors x4 |
| ESCs | BLHeli S 20A ESCs x4 |
| Propellers | 1045 propellers |
| Power distribution | X500 V2 PDB with XT60 battery plug and XT30 ESC/peripheral plugs |
| Motor outputs | MAIN1 to MAIN4 |
| RC input | SBUS receiver |
| Current transmitter | RadioMaster Boxer |
| Ground station | QGroundControl |

## Airframe Notes

The current vehicle is the Holybro X500 V2 development platform. The frame kit includes preinstalled motors, ESCs, propellers, and power distribution hardware. The current project adds the Raspberry Pi 5 companion computer and Intel RealSense D435i camera for visual following.

## Pi to Pixhawk Serial Link

| Signal | Connection |
| --- | --- |
| Pi serial device | `/dev/serial0 -> /dev/ttyAMA0` |
| Pi TX | GPIO14 / pin 8 |
| Pi RX | GPIO15 / pin 10 |
| Pixhawk port | TELEM2 |
| Baud rate | 57600 |
| Wiring rule | TX to RX, RX to TX, shared GND |

Wiring:

```text
PX4 TELEM2 TX -> Pi pin 10 / GPIO15 / RX
PX4 TELEM2 RX -> Pi pin 8  / GPIO14 / TX
PX4 TELEM2 GND -> Pi GND
```

## PX4 Parameters

Known working settings:

```text
MAV_1_CONFIG = TELEM2
SER_TEL2_BAUD = 57600
UXRCE_DDS_CFG = Disabled
MAV_1_FLOW_CTRL = Force off
```

Reboot the flight controller after changing serial or MAVLink parameters.

## Motor Output Mapping

```text
MAIN1 -> Motor1
MAIN2 -> Motor2
MAIN3 -> Motor3
MAIN4 -> Motor4
```

## RC Flight Modes

Current QGroundControl setup:

| Item | Value |
| --- | --- |
| Mode channel | Channel 7 |
| Low switch position | Stabilized |
| Middle switch position | Position |
| High switch position | Return |
| Arm switch | Channel 5 |
| Offboard switch | Unassigned |
| Emergency kill switch | Unassigned |

The Pi program enters Offboard mode. The pilot exits Offboard by switching back to Position or Stabilized.

## MAVLink Check

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Expected success indicators:

```text
Detected vehicle 1:1 on link 0
online system 1
Mode LOITER
Received parameters
```

## Still To Record

- PX4 firmware version.
- QGroundControl version.
- PX4 airframe selection.
- Actual battery capacity, C rating, and weight from the battery label.
- RC receiver model.
- Power module or BEC model if separate from the X500 V2 power distribution setup.
- Full takeoff weight with battery, Pi 5, RealSense, and mounts.
