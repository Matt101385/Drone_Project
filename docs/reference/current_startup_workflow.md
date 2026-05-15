# Current Startup Workflow

Last updated: 2026-05-15

## Purpose

This document summarizes the current way to start and maintain the drone project. It is not a full environment record and does not duplicate hardware or package version details.

For Pi 5 system versions, Python package versions, and RealSense installation details, use:

```text
docs/reference/pi5_environment_reference.md
```

## Current Main Program

Use this file as the current latest runtime program:

```text
07_latest_yolo_person_follow_click_target_stream.py
```

Historical name before cleanup:

```text
stream_mjpeg_yolo.py
```

The historical name should only be used when reading old notes or archived experiments.

## What This Program Does

The current main program is responsible for:

- Reading frames from the RealSense camera.
- Running YOLO-based person detection.
- Providing a Flask video stream.
- Supporting click-target / person-following style interaction.
- Acting as the current practical entry point for the drone vision workflow.

## Project Location

Current Raspberry Pi 5 vision project folder:

```text
/home/matt/matt_drone/follow_project
```

Short form:

```bash
~/matt_drone/follow_project
```

Current npm website folder:

```text
/home/matt/matt_drone/my-app
```

Short form:

```bash
~/matt_drone/my-app
```

GitHub repository:

```text
Matt101385/Drone_Project
```

## Python Vision Program Startup

Use this command group when starting the current vision program:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

Expected Python environment:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python
```

If `which python` shows `/usr/bin/python`, the virtual environment is not active correctly.

## Flask Video Stream

The Python vision program also provides a Flask video stream.

After the Python program is running, open the stream in a browser using the Raspberry Pi IP address.

Known example:

```text
http://10.0.0.105:5000
```

If the Pi IP changes, replace `10.0.0.105` with the current Pi IP.

## Website Startup

The npm website is stored in:

```text
~/matt_drone/my-app
```

To start only the web interface, use:

```bash
cd ~/matt_drone/my-app
npm run dev:web
```

Open:

```text
http://127.0.0.1:3000
```

The `npm run dev` command currently starts both `dev:web` and `dev:camera`. If `dev:camera` still points to an old Python path, `npm run dev` will fail and stop the web server.

Known old broken camera command from `package.json`:

```text
/home/matt/follow_project/.venv/bin/python /home/matt/follow_project/stream_mjpeg_yolo.py
```

The camera command should be updated to the current project path before using full `npm run dev`:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python /home/matt/matt_drone/follow_project/07_latest_yolo_person_follow_click_target_stream.py
```

Until that package script is updated, use `npm run dev:web` for the website and start the Python vision program separately.

## Pixhawk Heartbeat Check

Use this check to confirm the Pi can communicate with Pixhawk through MAVLink.

Start MAVProxy with:

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

If this heartbeat does not appear, check Pixhawk power, serial wiring, baudrate, and the `/dev/serial0` device path.

## Startup Order

For the full current workflow, start these in separate terminals as needed:

1. Python vision program:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

2. NPM website only:

```bash
cd ~/matt_drone/my-app
npm run dev:web
```

3. Pixhawk heartbeat check:

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Then open the relevant browser pages:

```text
Flask stream: http://10.0.0.105:5000
NPM website:  http://127.0.0.1:3000
```

## Important Project Files

Current runtime files:

```text
07_latest_yolo_person_follow_click_target_stream.py
realsense_reader_module.py
models/yolo11n.pt
models/yolov8n.pt
models/detect.tflite
models/labelmap.txt
```

Current website folder:

```text
~/matt_drone/my-app
```

Reference documentation:

```text
docs/reference/current_startup_workflow.md
docs/reference/pi5_environment_reference.md
docs/reference/project_file_structure_reference.md
docs/reference/realsense_d435i_reference.md
docs/reference/pixhawk_px4_reference.md
```

Historical notes:

```text
docs/project_notes/
```

Old experiments:

```text
archive/experiments/
```

## What To Update When The Main Program Changes

When a new script becomes the latest startup program, update this document in these places:

1. `Current Main Program`.
2. `Python Vision Program Startup`.
3. `What This Program Does`, if the behavior changed.
4. `Important Project Files`, if new required files were added.
5. `Flask Video Stream`, if the Python stream port or URL pattern changed.
6. `Website Startup`, if the website folder, command, or port changed.
7. `Pixhawk Heartbeat Check`, if the MAVLink device, baudrate, or success output changed.

Do not add package versions here. Put version changes in:

```text
docs/reference/pi5_environment_reference.md
```

## GitHub Sync Rule

GitHub does not update automatically after editing local files on the Pi 5.

After making a code or documentation change, save it with:

```bash
git status
git add .
git commit -m "Describe the change"
git push origin main
```

Runtime files should stay local and should not be committed.

Ignored examples:

```text
__pycache__/
logs/
.venv/
.env
*.log
color.jpg
depth.jpg
realsense_color.jpg
realsense_depth.jpg
models/test.jpg
```

## Short Project Summary

The current vision entry point is:

```text
07_latest_yolo_person_follow_click_target_stream.py
```

It runs from:

```text
~/matt_drone/follow_project
```

It should be started inside:

```text
.venv
```

The npm website runs from:

```text
~/matt_drone/my-app
```

Start the website only with:

```text
npm run dev:web
```

The Pixhawk heartbeat check runs inside:

```text
~/px4env
```

The common browser URLs are:

```text
Flask stream: http://10.0.0.105:5000
NPM website:  http://127.0.0.1:3000
```

Use `docs/reference/` for current working references. Use `docs/project_notes/` for historical progress notes. Use `archive/experiments/` for old scripts that are no longer the current startup program.
