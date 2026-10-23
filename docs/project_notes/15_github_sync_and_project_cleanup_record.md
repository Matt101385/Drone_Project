# 15 GitHub Sync and Project Cleanup Record

## Purpose

Record GitHub upload, project cleanup, and environment repair decisions.

## Current Main Program

Latest main program:

```bash
07_latest_yolo_person_follow_click_target_stream.py
```

Original name:

```bash
stream_mjpeg_yolo.py
```

Features:

- RealSense color and depth streams.
- YOLO person detection.
- Browser MJPEG stream.
- Click-to-select target.
- Target lock.
- Distance reading.
- Yaw and forward-command preview.

## File Organization

Root should keep the current runtime files:

```text
07_latest_yolo_person_follow_click_target_stream.py
realsense_reader_module.py
models/
yolo11n.pt
yolov8n.pt
.gitignore
.gitattributes
```

Experiments should live in:

```text
archive/experiments/
```

Do not upload runtime outputs:

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

## Virtual Environment Issue

The project moved from:

```text
~/follow_project
```

to:

```text
~/matt_drone/follow_project
```

After the move, `.venv` became path-confused. The shell showed `(.venv)`, but `which python` returned `/usr/bin/python`.

Correct output should be:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python
```

## Dependency Notes

YOLO dependencies:

```text
ultralytics
torch
torchvision
opencv-python
flask
numpy
```

Use a larger temp directory for pip if `/tmp` is too small:

```bash
mkdir -p ~/pip_tmp
TMPDIR=~/pip_tmp python -m pip install --no-cache-dir <package>
```

RealSense binding location:

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
```

Copy into venv:

```bash
cp -r /usr/local/lib/python3.13/dist-packages/pyrealsense2 \
  /home/matt/matt_drone/follow_project/.venv/lib/python3.13/site-packages/
```

## Key Takeaway

The code was not damaged. The main issue was virtual-environment path confusion after moving the project directory.
