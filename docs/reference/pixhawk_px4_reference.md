# Pixhawk / PX4 Reference

## Current Role

Pixhawk 6X is the flight controller. PX4 runs the flight-control stack. The Raspberry Pi 5 sends MAVLink/MAVSDK commands through the Pixhawk TELEM2 serial port.

## Confirmed Hardware

| Field | Value |
| --- | --- |
| Flight controller | Pixhawk 6X |
| Firmware stack | PX4 |
| Battery type | 4S LiPo |
| Motor outputs | MAIN1 to MAIN4 |
| RC input | SBUS receiver |
| Current transmitter | RadioMaster Boxer |
| Ground station | QGroundControl |

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
- GPS module model.
- Battery capacity, C rating, and weight.
- Motor, ESC, propeller, and frame model.
- Power module or BEC model.
