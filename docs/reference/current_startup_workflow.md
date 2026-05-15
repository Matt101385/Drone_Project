# Current Startup Workflow

Last updated: 2026-05-15

## Purpose

This document records the current startup procedure for the drone project. It is written so that the project can be reopened and run in the future, even after a long break.

Use this file as the main operational checklist before running the latest vision and drone-following program.

## Current Project Summary

The project currently runs on a Raspberry Pi 5 and uses a RealSense camera with a YOLO-based Python program. The latest main program starts a web video stream and supports person-following / click-target style interaction.

Current main script:

```text
07_latest_yolo_person_follow_click_target_stream.py
```

Current project folder on the Raspberry Pi 5:

```text
/home/matt/matt_drone/follow_project
```

Short path form:

```bash
~/matt_drone/follow_project
```

GitHub repository:

```text
Matt101385/Drone_Project
```

## Hardware Needed

Before starting the program, prepare the following hardware:

- Raspberry Pi 5.
- RealSense D435i camera.
- Power supply for the Raspberry Pi 5.
- Network connection to the Raspberry Pi 5.
- Laptop or desktop computer for SSH / VS Code Remote SSH.
- Pixhawk / PX4 flight controller, if testing drone control features.
- Drone battery and safety equipment, if testing with motors or propellers.

## Safety Notes

Before running anything connected to a real drone:

1. Remove propellers during software testing.
2. Keep the drone on a stable surface.
3. Confirm emergency stop / power disconnect is available.
4. Test camera and web stream first before enabling any flight-control behavior.
5. Do not test autonomous motion indoors unless the drone is physically safe and restrained.

## Expected Software Environment

The Pi 5 environment is recorded in:

```text
docs/reference/pi5_environment_reference.md
```

Current known environment:

```text
Raspberry Pi model: Raspberry Pi 5 Model B Rev 1.1
OS version: Debian GNU/Linux 13 (trixie), DEBIAN_VERSION_FULL=13.4
Kernel version: 6.12.75+rpt-rpi-2712
Python version: Python 3.13.5
OpenCV version: cv2 4.13.0
Ultralytics version: 8.4.46
Torch version: 2.11.0+cu130
Torchvision version: 0.26.0+cu130
RealSense Python binding: pyrealsense2 import ok
Node.js version: v20.19.2
npm version: 9.2.0
```

## Step 1: Power On the System

1. Power on the Raspberry Pi 5.
2. Connect the RealSense D435i camera to the Pi 5.
3. If Pixhawk is needed, connect it to the Pi 5 with the expected USB or serial connection.
4. Wait until the Pi 5 fully boots.
5. Make sure the Pi 5 is connected to the same network as the computer used for SSH.

## Step 2: Connect to the Raspberry Pi 5

Use VS Code Remote SSH or a terminal.

Known SSH target shown in past workspace screenshots:

```text
10.0.0.105
```

Example SSH command:

```bash
ssh matt@10.0.0.105
```

If the IP address changes, find the Pi address from the router, Raspberry Pi desktop, or network scanner.

## Step 3: Go to the Project Folder

Run:

```bash
cd ~/matt_drone/follow_project
```

Confirm the folder contains the main script:

```bash
ls
```

You should see:

```text
07_latest_yolo_person_follow_click_target_stream.py
realsense_reader_module.py
archive/
models/
```

## Step 4: Activate the Python Virtual Environment

Run:

```bash
source .venv/bin/activate
```

The terminal prompt should show:

```text
(.venv)
```

Then confirm Python points to the project virtual environment:

```bash
which python
```

Expected result:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python
```

If it shows `/usr/bin/python`, the virtual environment is not active correctly.

## Step 5: Check Important Python Packages

Run this quick check before starting the program:

```bash
python - <<'PY'
import cv2
import ultralytics
import torch
import torchvision
import pyrealsense2 as rs

print('cv2:', cv2.__version__)
print('ultralytics:', ultralytics.__version__)
print('torch:', torch.__version__)
print('torchvision:', torchvision.__version__)
print('pyrealsense2: import ok')
PY
```

Expected known versions from 2026-05-15:

```text
cv2: 4.13.0
ultralytics: 8.4.46
torch: 2.11.0+cu130
torchvision: 0.26.0+cu130
pyrealsense2: import ok
```

## Step 6: Check RealSense Connection

Make sure the RealSense camera is plugged in.

Optional system check:

```bash
lsusb
```

Look for an Intel / RealSense USB device.

If `pyrealsense2` fails to import, check the installed system files:

```bash
ls -l /usr/local/lib/python3.13/dist-packages | grep pyrealsense || true
ls -l /usr/local/lib | grep librealsense || true
```

Known RealSense files:

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
/usr/local/lib/librealsense2.so
/usr/local/lib/librealsense2.so.2.56
/usr/local/lib/librealsense2-gl.so
/usr/local/lib/librealsense2-gl.so.2.56
```

If `pyrealsense2` exists in the system path but not inside the virtual environment, copy it into the active `.venv`:

```bash
cp -r /usr/local/lib/python3.13/dist-packages/pyrealsense2 \
  /home/matt/matt_drone/follow_project/.venv/lib/python3.13/site-packages/
```

Then test again:

```bash
python -c "import pyrealsense2 as rs; print('pyrealsense2 ok')"
```

## Step 7: Start the Latest Main Program

From the project folder with `.venv` active, run:

```bash
python 07_latest_yolo_person_follow_click_target_stream.py
```

This is the current latest program.

Historical name before cleanup:

```text
stream_mjpeg_yolo.py
```

Do not use the old historical name unless checking archived experiments.

## Step 8: Open the Web Stream

After the program starts, open a browser on the laptop or desktop.

Use the Pi 5 IP address and the Flask port used by the program.

Common example:

```text
http://10.0.0.105:5000
```

If the Pi IP address changes, replace `10.0.0.105` with the current Pi IP.

If the page does not open:

1. Confirm the Python program is still running.
2. Confirm the Pi and computer are on the same network.
3. Check whether the program printed a Flask URL in the terminal.
4. Check whether the port is still `5000` in the Python script.
5. Try opening the page from the Pi itself first, then from another computer.

## Step 9: Normal Shutdown

To stop the running program, go to the terminal running the Python script and press:

```text
Ctrl+C
```

Wait for the terminal prompt to return.

If RealSense or camera access becomes stuck after repeated runs, unplug and reconnect the camera, then restart the script.

## Step 10: Before Editing Code

Always check Git status before making changes:

```bash
git status
```

This shows whether there are local changes that have not been saved to GitHub.

If the repo is behind GitHub, update first:

```bash
git pull origin main
```

Then edit the code.

## Step 11: Save Code Changes to GitHub

After editing and testing, run:

```bash
git status
git add .
git commit -m "Describe the change"
git push origin main
```

Example:

```bash
git add .
git commit -m "Update YOLO follow stream startup logic"
git push origin main
```

## Optional Fast Sync Command

A shell helper may be added on the Pi 5 to make GitHub sync faster.

Example helper in `~/.bashrc`:

```bash
function sync() {
  cd ~/matt_drone/follow_project || return
  git add .
  git commit -m "$1"
  git push origin main
}
```

Then use:

```bash
sync "Update startup workflow"
```

Only use this after checking that the files being committed are correct.

## Files That Should Stay in GitHub

Important source files and documents should be kept in GitHub:

```text
07_latest_yolo_person_follow_click_target_stream.py
realsense_reader_module.py
models/yolo11n.pt
models/yolov8n.pt
models/detect.tflite
models/labelmap.txt
archive/experiments/
docs/project_notes/
docs/reference/
```

## Files That Should Not Be Uploaded

Runtime output, cache, logs, environment folders, and temporary images should not be committed.

These are ignored by `.gitignore`:

```text
__pycache__/
*.pyc
logs/
*.log
.venv/
.env
color.jpg
depth.jpg
realsense_color.jpg
realsense_depth.jpg
models/test.jpg
```

## Project Organization

Current intended organization:

```text
follow_project/
  07_latest_yolo_person_follow_click_target_stream.py
  realsense_reader_module.py
  models/
  archive/
    experiments/
  docs/
    project_notes/
    reference/
  .gitignore
  .gitattributes
```

`docs/project_notes/` is for historical notes.

`docs/reference/` is for current working instructions and long-term recovery documents.

`archive/experiments/` is for old experimental scripts that should be kept for history but are not the current startup program.

## Common Problem: ModuleNotFoundError for ultralytics

If this happens:

```text
ModuleNotFoundError: No module named 'ultralytics'
```

First check Python:

```bash
which python
```

If it shows:

```text
/usr/bin/python
```

then `.venv` is not active correctly.

Reactivate:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
hash -r
which python
```

Expected:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python
```

## Common Problem: ModuleNotFoundError for pyrealsense2

If this happens:

```text
ModuleNotFoundError: No module named 'pyrealsense2'
```

Check system installation:

```bash
ls -l /usr/local/lib/python3.13/dist-packages | grep pyrealsense
```

If found, copy it into the virtual environment:

```bash
cp -r /usr/local/lib/python3.13/dist-packages/pyrealsense2 \
  /home/matt/matt_drone/follow_project/.venv/lib/python3.13/site-packages/
```

Then test:

```bash
python -c "import pyrealsense2 as rs; print('pyrealsense2 ok')"
```

## Common Problem: pip Says No Space Left on Device

If pip fails with:

```text
No space left on device
```

The SD card may still have space, but `/tmp` may be small.

Check disk space:

```bash
df -h
```

Use a larger temporary folder:

```bash
mkdir -p ~/pip_tmp
TMPDIR=~/pip_tmp python -m pip install --no-cache-dir <package>
```

## Common Problem: GitHub Does Not Update After Editing

GitHub does not automatically update when a file is edited locally.

You must run:

```bash
git add .
git commit -m "Describe the change"
git push origin main
```

In VS Code, a file with `M` next to it means the file is modified locally but not committed yet.

## Common Problem: Long File Name Breaks Across Lines

If a command is accidentally split across two terminal lines, Python may fail with a missing file error.

Correct command:

```bash
python 07_latest_yolo_person_follow_click_target_stream.py
```

Incorrect broken command example:

```text
python 07_latest_yolo_person_follow_click_target_s
tream.py
```

Use tab completion to avoid mistakes:

```bash
python 07<TAB>
```

## Future Maintenance Rule

When the latest startup program changes, update this file immediately.

At minimum, update:

1. `Current main script`.
2. `Step 7: Start the Latest Main Program`.
3. Any web URL or port changes.
4. Any new hardware startup steps.
5. Any new dependency or environment requirements.

## Quick Start Summary

For normal startup, the shortest working sequence is:

```bash
ssh matt@10.0.0.105
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

Then open:

```text
http://10.0.0.105:5000
```
