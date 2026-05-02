# RealSense D435i Reference

## Purpose

This document records the current Intel RealSense D435i setup for the drone project.

## Current Role

The RealSense D435i provides:

- Color stream for YOLO person detection.
- Depth stream for target-distance estimation.
- Camera input for browser MJPEG streaming.

## Current Main Program

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

## Known Working Stream Settings

The latest YOLO program uses:

```text
Color stream: 640 x 480
Depth stream: 640 x 480
FPS: 15
Color format: bgr8
Depth format: z16
```

Earlier basic stream programs used 640 x 480 at 30 FPS.

## RealSense Python Binding

Known location on Pi 5:

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
```

If the current `.venv` cannot import it, copy it into the virtual environment:

```bash
cp -r /usr/local/lib/python3.13/dist-packages/pyrealsense2 \
  /home/matt/matt_drone/follow_project/.venv/lib/python3.13/site-packages/
```

Test:

```bash
python -c "import pyrealsense2 as rs; print('realsense ok')"
```

## librealsense Files

Known files from earlier Pi 5 recovery:

```text
/usr/local/lib/librealsense2.so.2.56
/usr/local/lib/librealsense2-gl.so.2.56
```

udev rule:

```text
99-realsense-libusb.rules
```

## Useful Checks

Check USB detection:

```bash
lsusb | grep -i realsense
```

Check RealSense Python import:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python -c "import pyrealsense2 as rs; print('realsense ok')"
```

Check available RealSense files:

```bash
ls -l /usr/local/lib/python3.13/dist-packages | grep pyrealsense
ls -l /usr/local/lib | grep librealsense
```

## Common Problems

### `ModuleNotFoundError: No module named 'pyrealsense2'`

Cause: current virtual environment does not contain the manually installed RealSense binding.

Fix: copy `pyrealsense2` from `/usr/local/lib/python3.13/dist-packages/` into the current `.venv` site-packages.

### Camera stream exists but browser looks wrong

Possible causes:

- Multiple backend processes running.
- Old script still running.
- Browser cache or stale stream.
- Processing error after frame capture.

First check the raw stream directly:

```text
http://localhost:8000/stream
```

## Fields to Update Later

```text
RealSense model: Intel RealSense D435i
Serial number: TODO
Firmware version: TODO
librealsense version: TODO
pyrealsense2 version/build: TODO
USB mode: TODO
Working resolution/FPS confirmed on current Pi: TODO
```

Use `realsense-viewer` or RealSense command-line tools to collect exact firmware/device details when needed.
