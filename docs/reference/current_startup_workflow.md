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
- Providing a web video stream through Flask.
- Supporting click-target / person-following style interaction.
- Acting as the current practical entry point for the drone vision workflow.

## Project Location

Current Raspberry Pi 5 project folder:

```text
/home/matt/matt_drone/follow_project
```

Short form:

```bash
~/matt_drone/follow_project
```

GitHub repository:

```text
Matt101385/Drone_Project
```

## Runtime Entry Point

Use this command group when starting the current program:

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

## Web Stream

After the program starts, open the Flask stream in a browser using the Raspberry Pi IP address.

Known example:

```text
http://10.0.0.105:5000
```

If the Pi IP changes, replace `10.0.0.105` with the current Pi IP.

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
2. `Runtime Entry Point`.
3. `What This Program Does`, if the behavior changed.
4. `Important Project Files`, if new required files were added.
5. `Web Stream`, if the port or URL pattern changed.

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

The current project entry point is:

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

It opens a browser-accessible stream, usually at:

```text
http://10.0.0.105:5000
```

Use `docs/reference/` for current working references. Use `docs/project_notes/` for historical progress notes. Use `archive/experiments/` for old scripts that are no longer the current startup program.
