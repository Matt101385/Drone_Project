# 10 PX4 TELEM2 Connection Success - 2026-04-11

## Purpose

Record the final successful Raspberry Pi 5 to PX4 serial connection.

## Working Setup

```text
Pi 5 GPIO serial
/dev/serial0 -> /dev/ttyAMA0
GPIO14 = TXD0
GPIO15 = RXD0
PX4 TELEM2
Baud rate: 57600
```

Use TELEM2, not TELEM1.

## Wiring

```text
PX4 TELEM2 TX -> Pi pin 10 / GPIO15 / RX
PX4 TELEM2 RX -> Pi pin 8  / GPIO14 / TX
PX4 TELEM2 GND -> Pi GND
```

## PX4 Parameters

```text
MAV_1_CONFIG = TELEM2
SER_TEL2_BAUD = 57600
UXRCE_DDS_CFG = Disabled
MAV_1_FLOW_CTRL = Force off
```

## Pi Serial Check

```bash
ls -l /dev/ttyAMA0 /dev/serial0
pinctrl get 14
pinctrl get 15
```

## MAVProxy

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

## Success Output

```text
Detected vehicle 1:1 on link 0
online system 1
Mode LOITER
Received 1148 parameters
```

## Key Takeaway

The real PX4 serial link works through Pi GPIO serial to PX4 TELEM2 at 57600 baud with flow control forced off.
