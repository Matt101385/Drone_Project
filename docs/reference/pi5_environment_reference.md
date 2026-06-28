# Pi 5 Environment Reference

## Current Role

The Raspberry Pi 5 is the onboard companion computer. It runs the RealSense camera pipeline, YOLO person detection, browser video stream, and optional Pixhawk/PX4 Offboard control.

## Confirmed Device Data

Collected from the Pi terminal.

| Field | Value |
| --- | --- |
| Pi model | Raspberry Pi 5 Model B Rev 1.1 |
| Hostname | MattZhang |
| Architecture | aarch64 GNU/Linux |
| Kernel | Linux 6.12.75+rpt-rpi-2712 |
| OS build | Debian 1:6.12.75-1+rpt1 |
| Kernel build date | 2026-03-11 |
| Python | Python 3.13.5 |
| Main project path | `~/matt_drone/follow_project` |
| Main virtual environment | `~/matt_drone/follow_project/.venv` |

Raw `uname -a` output:

```text
Linux MattZhang 6.12.75+rpt-rpi-2712 #1 SMP PREEMPT Debian 1:6.12.75-1+rpt1 (2026-03-11) aarch64 GNU/Linux
```

## Start Environment

Run this first in each Pi terminal:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
```

Check:

```bash
which python
python --version
```

Expected Python version:

```text
Python 3.13.5
```

## Confirmed Project Stack

| Layer | Current use |
| --- | --- |
| Camera access | Intel RealSense D435i through Python |
| Computer vision | YOLO11n |
| Web stream | WebRTC / browser interface on port `8080` |
| Flight-control link | MAVSDK / MAVLink to Pixhawk over serial |
| Safety layer | `scripts/safety_supervisor_v2.py` |

## Notes

- The old `~/follow_project` path is historical.
- The active project path is `~/matt_drone/follow_project`.
- If `which python` points to `/usr/bin/python`, the virtual environment is not active.
