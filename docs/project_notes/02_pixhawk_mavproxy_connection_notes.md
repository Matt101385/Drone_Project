# 02 Pixhawk MAVProxy Connection Notes

## Purpose

Record the early Pixhawk MAVLink connection workflow from Raspberry Pi.

## MAVProxy Command

```bash
~/.local/bin/mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Exit:

```text
Ctrl + C
```

## Vision Environment

```bash
source ~/vision_env/bin/activate
```

Common scripts:

```bash
python ~/follow_project/realsense_depth.py
python ~/follow_project/stream_mjpeg.py
python ~/follow_project/stream_face_mjpeg.py
```

View logs:

```bash
tail -n 20 ~/follow_project/logs/stream_$(date +%Y%m%d).log
```

## Verified Capabilities

RealSense:

- Color stream works.
- Image saving works.
- MJPEG stream works.
- Face detection works.
- `dx` and `dy` can be computed.

Pixhawk:

- MAVLink path works.
- Serial communication works.
- Heartbeat works.

## Status

```text
Vision layer: working
Flight-controller communication: working
Closed-loop control: not connected yet
```
