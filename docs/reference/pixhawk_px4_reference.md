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

## Radio / Flight Mode Switch Configuration

Current transmitter:

```text
RadioMaster Boxer
```

Current QGroundControl flight mode setup:

```text
Mode Channel: Channel 7
```

Because the selected Boxer switch is a three-position switch, it effectively lands on three QGroundControl flight mode slots:

```text
Low position:    Flight Mode 1 -> Stabilized
Middle position: Flight Mode 4 -> Position
High position:   Flight Mode 6 -> Return
```

Current switch assignments:

```text
Arm Switch: Channel 5
Return Switch: Unassigned
Loiter / Hold Switch: Unassigned
Emergency Kill Switch: Unassigned
Offboard Switch Channel: Unassigned
```

Current intended control logic:

```text
Manual takeoff / manual takeover: Position
Fallback when Position is not reliable: Stabilized
Autonomous follow control: Offboard, entered by the Pi program
Emergency navigation: Return
```

Offboard is intentionally not assigned to a transmitter switch right now. The Pi program enters Offboard. The pilot exits Offboard by switching Channel 7 back to Position or Stabilized.

## Flight Mode Notes

### Stabilized

Stabilized keeps the aircraft attitude level, but it does not hold horizontal position or altitude automatically.

If there is wind, the aircraft can drift. The pilot must actively control position and throttle.

Use Stabilized as the fallback mode when Position is not available or position estimation is not trustworthy.

### Position

Position uses position estimation, such as GPS outdoors, to hold horizontal position and altitude.

When position estimate is healthy, Position is the normal manual takeover mode for follow testing. If the pilot releases the sticks, the aircraft should try to hold position.

If QGroundControl reports `X/Y position control Error`, Position is not ready and should not be used for Offboard follow testing.

### Return

Return commands the aircraft to return to its home position when GPS and home position are valid.

Return is useful as an emergency navigation mode, but it should not replace direct pilot takeover for close-range follow testing.

### Offboard

Offboard is controlled by the companion computer. In this project, the Pi sends velocity and yaw commands through the safety layer to the Pixhawk.

RC sticks do not directly fly the vehicle while Offboard is active. The pilot must switch out of Offboard to Position or Stabilized to take back control.

### Emergency Kill

Emergency Kill is currently unassigned.

Before any prop-on real flight, assign Emergency Kill to a separate switch that is hard to hit accidentally and test it with props removed.

Emergency Kill is the last-resort motor stop. It does not recover or land the vehicle.

Use Emergency Kill only when:

```text
- The aircraft is moving toward a person.
- The aircraft is uncontrollable.
- The aircraft has crashed or flipped and motors are still spinning.
- Switching back to Position, Stabilized, Return, or Hold does not stop the danger.
```

Do not use Emergency Kill for:

```text
- Normal Offboard exit.
- Normal manual takeover.
- Normal landing.
- Small follow-control errors.
```

Normal takeover order:

```text
1. Switch to Position.
2. If Position is not available, switch to Stabilized.
3. Use Return / Hold if appropriate.
4. Use Emergency Kill only as the final last-resort action.
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
