# Pixhawk / PX4 Reference

## Purpose

This document records the current Pixhawk / PX4 connection reference for the drone project.

## Current Working Connection

The successful Raspberry Pi 5 to PX4 connection uses:

```text
Pi 5 GPIO serial
/dev/serial0 -> /dev/ttyAMA0
GPIO14 = TXD0
GPIO15 = RXD0
PX4 TELEM2
Baud rate: 57600
```

Important rule:

```text
Use TELEM2, not TELEM1.
```

## Wiring

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

After changing parameters, reboot the flight controller.

## Pi Serial Check

```bash
ls -l /dev/ttyAMA0 /dev/serial0
pinctrl get 14
pinctrl get 15
```

Expected:

```text
/dev/serial0 -> ttyAMA0
GPIO14 = TXD0
GPIO15 = RXD0
```

## MAVProxy Startup

Activate environment:

```bash
cd ~
source ~/px4env/bin/activate
```

Start connection:

```bash
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Successful output:

```text
Detected vehicle 1:1 on link 0
online system 1
Mode LOITER
Received 1148 parameters
```

## Safety Direction

The project should use a reusable safety layer for future offboard programs.

Safety layers:

1. Command limiting.
2. Program supervisor.
3. PX4 built-in failsafes.

Manual override rule:

```text
If PX4 leaves OFFBOARD mode, the program stops sending commands immediately.
```

## Fields to Update Later

```text
PX4 version: TODO
QGroundControl version: TODO
Flight controller model / firmware target: TODO
Airframe: TODO
Battery setup: TODO
RC setup: TODO
Telemetry radio status: TODO
```

## Commands / Checks to Collect More Info

From QGroundControl, record:

- PX4 firmware version.
- Airframe.
- MAVLink parameter values.
- Safety settings.
- Battery setup.

From Pi:

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```
