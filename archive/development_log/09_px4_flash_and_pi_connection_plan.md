# 09 PX4 Flashing and Pi Connection Plan

## Purpose

Record the transition from ArduPilot to PX4 and the plan for Raspberry Pi companion-computer connection.

## Goal

```text
Pi reads visual information
Pi sends control commands to PX4
Drone follows visual target
```

## PX4 Setup

QGroundControl opened and detected the flight controller. The controller was initially on ArduPilot, then moved to PX4 Stable Release after backing up old settings.

Reviewed PX4 pages:

- Actuators.
- Safety.
- Power.
- Flight Modes.
- Parameters.

## Motor Mapping

```text
MAIN1 -> Motor1
MAIN2 -> Motor2
MAIN3 -> Motor3
MAIN4 -> Motor4
```

## Interface Planning

Initial plan:

```text
SBUS -> receiver
TELEM1 -> Raspberry Pi 5
TELEM2 -> telemetry radio
TELEM3 -> unused
```

Later, the successful setup used TELEM2 for the Pi.

## Parameters Discussed

```text
MAV_0_CONFIG
MAV_1_CONFIG
MAV_2_CONFIG
SER_TEL1_BAUD
SER_TEL2_BAUD
MAV_0_FLOW_CTRL
```

For three-wire UART, flow control should be forced off.

## Early MAVProxy Work

A dedicated environment was created:

```text
~/mavenv
```

MAVProxy could run but initially waited for heartbeat:

```text
Waiting for heartbeat from /dev/serial0
link 1 down
```

## Serial Checks

```bash
ls -l /dev/serial0
ls /dev/ttyAMA* /dev/ttyS*
stty -F /dev/serial0 57600
cat /dev/serial0
```

## Key Takeaway

At this stage, software installation was mostly solved; the remaining issue was physical serial / PX4 port configuration.
