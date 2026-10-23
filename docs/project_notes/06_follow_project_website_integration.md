# 06 `follow_project` and Website Integration

## Purpose

Record how the camera/AI project connects to the web dashboard.

## Directory Roles

```text
~/follow_project  -> camera and AI project
~/my-app          -> Next.js website
~/librealsense    -> RealSense source/build folder
```

## Main Environment

Standardized environment:

```text
~/follow_project/.venv
```

Verified libraries:

- `pyrealsense2`
- `opencv`
- `ultralytics`

This allowed RealSense and YOLO to run in one environment.

## Main Program

```text
stream_mjpeg_yolo.py
```

It originally used `yolov8n.pt`, then was upgraded to `yolo11n.pt`.

## Architecture

```text
Python handles RealSense + YOLO stream
Next.js displays the stream and system dashboard
```

## Startup

YOLO stream:

```bash
cd ~/follow_project
source .venv/bin/activate
python stream_mjpeg_yolo.py
```

Website:

```bash
cd ~/my-app
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Key Takeaway

The project became a clean two-part system: Python for vision, Next.js for the UI.
