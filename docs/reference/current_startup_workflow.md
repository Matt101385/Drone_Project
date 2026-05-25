# Current Startup Workflow

Last updated: 2026-05-24

## Purpose

This document summarizes the current startup workflow for the Raspberry Pi 5 drone follow project. It focuses on what to run and in what order. For package versions, RealSense installation details, and hardware references, use the other files in `docs/reference/`.

## Current Main Program

Use this file as the current real-follow safety entry point:

```text
scripts/11_follow_safe.py
```

This is the current main program for:

- RealSense color/depth capture.
- YOLO person detection.
- WebRTC video stream on port `8080`.
- Click-to-select target.
- Dry follow command preview by default.
- Optional real Pixhawk control with `FOLLOW_REAL=1`.
- Safety supervision through `scripts/safety_supervisor_v2.py`.

## Active Scripts

```text
scripts/07_latest_yolo_person_follow_click_target_stream.py
```

Validated MJPEG click-target stream. Keep it as a known-good visual baseline and website/backend compatibility script.

```text
scripts/10_webrtc_follow_udp_test.py
```

WebRTC follow/UDP intermediate validation script.

```text
scripts/11_follow_safe.py
```

Current main WebRTC + safety follow script.

```text
scripts/12_takeoff_hover_land_test.py
```

PX4/MAVSDK takeoff, hover, and land smoke test. Run this before any real follow testing.

## Project Locations

Current Raspberry Pi 5 Python project folder:

```text
~/matt_drone/follow_project
```

GitHub repository:

```text
Matt101385/Drone_Project
```

Current dashboard website prototype:

```text
~/matt_drone/my-app
```

`my-app` is still a separate local dashboard prototype. Do not push it until the repository is intentionally reorganized.

## Development Network

Use normal Wi-Fi while developing or copying files:

```text
Pi IP: 10.0.0.105
```

Use the Pi hotspot only in the field:

```bash
sudo nmcli connection up drone
```

When connected to the `drone` hotspot:

```text
Pi IP: 10.42.0.1
```

Return to normal Wi-Fi:

```bash
sudo nmcli connection down drone
sudo nmcli connection up CharlesZhang
```

## Common Setup

Run this first in every Pi terminal:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
```

Expected Python environment:

```text
~/matt_drone/follow_project/.venv/bin/python
```

If `which python` shows `/usr/bin/python`, the virtual environment is not active correctly.

## Start Current Follow Program In Dry Mode

Dry mode is the default. It runs vision, target selection, status output, and command preview without sending Pixhawk movement commands.

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python -u scripts/11_follow_safe.py
```

Open from normal Wi-Fi:

```text
http://10.0.0.105:8080
```

Open from Pi hotspot:

```text
http://10.42.0.1:8080
```

Expected dry-mode terminal output includes:

```text
[DRY] FOLLOW_REAL is not 1; vision runs, Pixhawk commands are not sent.
```

## Start Real Follow Mode

Only use real follow after bench tests, takeoff/land smoke test, and outdoor dry-run checks pass.

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
FOLLOW_REAL=1 python -u scripts/11_follow_safe.py
```

Keep RC ready to switch out of Offboard immediately. Abort if the wrong target is locked, video freezes, position quality drops, or the aircraft moves unexpectedly.

## Takeoff Hover Land Smoke Test

Run this before real follow testing:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python -u scripts/12_takeoff_hover_land_test.py --addr serial:///dev/serial0:57600 --alt 2.5 --hover 8 --real
```

The script requires typing:

```text
TAKEOFF
```

Expected behavior:

- Connects to Pixhawk.
- Waits for health checks.
- Arms only after typed confirmation.
- Takes off to about `2.5 m`.
- Holds for about `8 s`.
- Lands automatically.

## Legacy MJPEG Visual Baseline

Use this if you need the older MJPEG stream behavior or the website proxy workflow:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python -u scripts/07_latest_yolo_person_follow_click_target_stream.py
```

Open:

```text
http://10.0.0.105:8000/stream
```

or from the hotspot:

```text
http://10.42.0.1:8000/stream
```

## Dashboard Website Prototype

The npm website/dashboard is stored in:

```text
~/matt_drone/my-app
```

Start website only:

```bash
cd ~/matt_drone/my-app
npm run dev
```

Start website plus the legacy MJPEG camera backend:

```bash
cd ~/matt_drone/my-app
npm run dev:all
```

Current `dev:camera` target:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python /home/matt/matt_drone/follow_project/scripts/07_latest_yolo_person_follow_click_target_stream.py
```

The website prototype still points at the `07` MJPEG backend. The real-follow WebRTC workflow uses `scripts/11_follow_safe.py` directly.

## Pixhawk Heartbeat Check

Use MAVProxy to confirm Pi-to-Pixhawk serial communication:

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Success output should include:

```text
Detected vehicle 1:1 on link 0
online system 1
Mode LOITER
```

If this heartbeat does not appear, check Pixhawk power, serial wiring, baudrate, and `/dev/serial0`.

## Recommended Field Test Order

1. Bench test without props:

```bash
python -u scripts/11_follow_safe.py
```

2. Outdoor takeoff/hover/land smoke test:

```bash
python -u scripts/12_takeoff_hover_land_test.py --addr serial:///dev/serial0:57600 --alt 2.5 --hover 8 --real
```

3. Outdoor follow dry run:

```bash
python -u scripts/11_follow_safe.py
```

4. Short real follow test:

```bash
FOLLOW_REAL=1 python -u scripts/11_follow_safe.py
```

## Important Files

Current runnable scripts and modules:

```text
scripts/07_latest_yolo_person_follow_click_target_stream.py
scripts/10_webrtc_follow_udp_test.py
scripts/11_follow_safe.py
scripts/12_takeoff_hover_land_test.py
scripts/realsense_reader_module.py
scripts/safety_supervisor_v2.py
```

Reference documentation:

```text
docs/reference/current_startup_workflow.md
docs/reference/project_file_structure_reference.md
docs/reference/pi5_environment_reference.md
docs/reference/pixhawk_px4_reference.md
docs/reference/realsense_d435i_reference.md
```

Field checklist:

```text
docs/field_ops/field_test_checklist.md
```

Old experiments:

```text
archive/experiments/
```

## Runtime Files Not To Commit

```text
__pycache__/
logs/
.venv/
.env
*.log
*.backup*
*.broken_backup*
*.before_transfer*
color.jpg
depth.jpg
realsense_color.jpg
realsense_depth.jpg
models/test.jpg
```

## GitHub Sync Rule

GitHub does not update automatically after editing local files on the Pi 5. After changing code, startup commands, project paths, package scripts, or reference documentation, commit and push the relevant files after Matt approves the update.

Use a clean local clone when possible:

```bash
git clone https://github.com/Matt101385/Drone_Project.git
cd Drone_Project
```

Then:

```bash
git status
git add <changed-files>
git commit -m "Describe the change"
git push origin main
```

## Short Summary

Current main follow program:

```text
scripts/11_follow_safe.py
```

Default mode:

```text
DRY, no Pixhawk movement commands
```

Real follow mode:

```text
FOLLOW_REAL=1 python -u scripts/11_follow_safe.py
```

Required smoke test before real follow:

```text
scripts/12_takeoff_hover_land_test.py
```

Common browser URL:

```text
http://<pi-ip>:8080
```
