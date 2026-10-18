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
| Main project path | `~/Drone_Project` (active path recorded in field checklist) |
| Main virtual environment | `~/Drone_Project/.venv` |

Raw `uname -a` output:

```text
Linux MattZhang 6.12.75+rpt-rpi-2712 #1 SMP PREEMPT Debian 1:6.12.75-1+rpt1 (2026-03-11) aarch64 GNU/Linux
```

## Start Environment

Run this first in each Pi terminal:

```bash
cd ~/Drone_Project
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
| Person detection | Hailo-10H via `src/hailo_person_detector.py` |
| Distance sensing | RealSense D435i depth; main program does not read LiDAR |
| Web stream | WebRTC / browser interface on port `8080` |
| Flight-control link | MAVSDK / MAVLink to Pixhawk over serial |
| Follow control | `PositionNedYaw` setpoints with PX4 NED feedback in `src/follow_drone.py` |

## Notes

- Active repository path recorded by the field checklist: `~/Drone_Project`; confirm on-device before running.
- Main program logs to `~/follow_project/logs`, a separate legacy output path; code behavior is unchanged.
- LiDAR model/interface/role still need recording; the main program does not consume its data.
- If `which python` points to `/usr/bin/python`, the virtual environment is not active.
