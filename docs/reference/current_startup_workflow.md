# Current Startup Workflow

Last updated: 2026-05-16

## Purpose

This document summarizes the current way to start and maintain the drone project. It is not a full environment record and does not duplicate hardware or package version details.

For Pi 5 system versions, Python package versions, and RealSense installation details, use:

```text
docs/reference/pi5_environment_reference.md
```

## Current Main Program

Use this file as the current latest Python runtime program:

```text
07_latest_yolo_person_follow_click_target_stream.py
```

Historical name before cleanup:

```text
stream_mjpeg_yolo.py
```

The historical name should only be used when reading old notes or archived experiments.

## What This Program Does

The current main Python program is responsible for:

- Reading frames from the RealSense camera.
- Running YOLO-based person detection.
- Providing a camera/video stream backend.
- Supporting click-target / person-following style interaction.
- Acting as the current practical entry point for the drone vision workflow.

## Project Locations

Current Raspberry Pi 5 Python vision project folder:

```text
/home/matt/matt_drone/follow_project
```

Short form:

```bash
~/matt_drone/follow_project
```

Current local dashboard website folder:

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

Important Git note: `follow_project` and `my-app` are currently separate local Git folders. `follow_project` is the main project that is synced with GitHub. `my-app` has a local commit for the dashboard prototype, but it should not be pushed until the repository structure is intentionally reorganized.

## Python Vision Program Startup

Use this command group when starting only the current Python vision program:

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

## Dashboard Website Startup

The npm website/dashboard is stored in:

```text
~/matt_drone/my-app
```

Current package script rule:

```text
npm run dev      = start website only
npm run dev:web  = start website only
npm run dev:all  = start website + Python camera backend
npm run dev:camera = start Python camera backend only
```

To start only the web interface:

```bash
cd ~/matt_drone/my-app
npm run dev
```

Equivalent explicit command:

```bash
cd ~/matt_drone/my-app
npm run dev:web
```

Open:

```text
http://127.0.0.1:3000
```

From another device on the same network, replace `127.0.0.1` with the Raspberry Pi IP address:

```text
http://<pi-ip-address>:3000
```

## Website Plus Camera Backend Startup

To start both the dashboard website and the Python camera backend together:

```bash
cd ~/matt_drone/my-app
npm run dev:all
```

Current `dev:camera` target:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python /home/matt/matt_drone/follow_project/07_latest_yolo_person_follow_click_target_stream.py
```

This means `npm run dev:all` depends on the Python virtual environment and current main program in `~/matt_drone/follow_project`.

## Dashboard Camera API

The dashboard proxies camera traffic through Next.js API routes.

Current frontend/backend route relationship:

```text
Dashboard image source: /api/realsense
Next.js stream proxy:  http://127.0.0.1:8000/stream
Click target proxy:    http://127.0.0.1:8000/select_target
```

If the website shows an error like:

```text
connect ECONNREFUSED 127.0.0.1:8000
```

that means the website is running, but the Python camera backend is not running or is not listening on port `8000`.

Fix by starting the backend:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

or start both services together from the website folder:

```bash
cd ~/matt_drone/my-app
npm run dev:all
```

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

For the full current workflow, start these as needed.

Option A: Start Python and website separately in two terminals.

Terminal 1, Python vision backend:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

Terminal 2, website only:

```bash
cd ~/matt_drone/my-app
npm run dev
```

Option B: Start website and Python camera backend together:

```bash
cd ~/matt_drone/my-app
npm run dev:all
```

Optional Pixhawk heartbeat check:

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Common browser pages:

```text
Dashboard website: http://127.0.0.1:3000
Camera backend:    http://127.0.0.1:8000/stream
```

If accessing from another device on the same network, replace `127.0.0.1` with the Pi IP address.

## Important Project Files

Current Python runtime files:

```text
07_latest_yolo_person_follow_click_target_stream.py
realsense_reader_module.py
models/yolo11n.pt
models/yolov8n.pt
models/detect.tflite
models/labelmap.txt
```

Current dashboard files in `~/matt_drone/my-app`:

```text
app/page.tsx
app/StreamViewer.tsx
app/api/realsense/route.ts
app/api/realsense/select-target/route.ts
system.ts
package.json
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
5. `Dashboard Camera API`, if the Python stream port or URL pattern changed.
6. `Dashboard Website Startup`, if the website folder, command, or port changed.
7. `Website Plus Camera Backend Startup`, if the npm scripts change.
8. `Pixhawk Heartbeat Check`, if the MAVLink device, baudrate, or success output changed.

Do not add package versions here. Put version changes in:

```text
docs/reference/pi5_environment_reference.md
```

## GitHub Sync Rule

GitHub does not update automatically after editing local files on the Pi 5.

When Matt changes code, startup commands, project paths, package scripts, or reference documentation, Codex should remind Matt if the change should be saved to GitHub. Codex should explain what should be committed and why, then wait for Matt's approval before committing or pushing.

For `follow_project`, after Matt approves a GitHub update, save it with:

```bash
cd ~/matt_drone/follow_project
git status
git add <changed-files>
git commit -m "Describe the change"
git push origin main
```

For `my-app`, do not push to GitHub yet. It currently has a local dashboard prototype commit, but the repository structure should be reorganized before publishing it to the shared GitHub repository.

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

The current Python vision entry point is:

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

The dashboard website runs from:

```text
~/matt_drone/my-app
```

Start the website only with:

```text
npm run dev
```

Start website plus Python camera backend with:

```text
npm run dev:all
```

The Pixhawk heartbeat check runs inside:

```text
~/px4env
```

The common browser URLs are:

```text
Dashboard website: http://127.0.0.1:3000
Camera backend:    http://127.0.0.1:8000/stream
```

Use `docs/reference/` for current working references. Use `docs/project_notes/` for historical progress notes. Use `archive/experiments/` for old scripts that are no longer the current startup program.
