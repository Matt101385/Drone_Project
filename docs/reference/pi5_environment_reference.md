# Pi 5 Environment Reference

## Purpose

This document records the current Raspberry Pi 5 environment used by the drone project.

## Current Role

The Raspberry Pi 5 is the main onboard / edge computer for:

- RealSense camera access.
- YOLO person-detection stream.
- Local Python runtime.
- Future Pixhawk / PX4 companion-computer control.

## Project Location

Current main project path:

```bash
~/matt_drone/follow_project
```

Historical path:

```bash
~/follow_project
```

Important note: moving the project from `~/follow_project` to `~/matt_drone/follow_project` caused `.venv` path confusion. The active Python should always be checked with:

```bash
which python
```

Expected result:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python
```

## Main Virtual Environment

Activate:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
```

Check Python:

```bash
which python
python -V
```

## Current Runtime Program

```bash
python scripts/07_latest_yolo_person_follow_click_target_stream.py
```

## Current Version Fields

Last updated from Pi 5 terminal output on 2026-05-15.

```text
Raspberry Pi model: Raspberry Pi 5 Model B Rev 1.1
OS version: Debian GNU/Linux 13 (trixie), DEBIAN_VERSION_FULL=13.4
Kernel version: Linux MattZhang 6.12.75+rpt-rpi-2712 #1 SMP PREEMPT Debian 1:6.12.75-1+rpt1 (2026-03-11) aarch64 GNU/Linux
Python version: Python 3.13.5
pip version: pip 26.1 from /home/matt/matt_drone/follow_project/.venv/lib/python3.13/site-packages/pip (python 3.13)
OpenCV version: cv2 4.13.0
Ultralytics version: 8.4.46
Torch version: 2.11.0+cu130
Torchvision version: 0.26.0+cu130
NumPy version: 2.4.4
Flask version: 3.1.3
RealSense Python binding: pyrealsense2 import ok
librealsense version/files: /usr/local/lib/librealsense2.so.2.56 and /usr/local/lib/librealsense2-gl.so.2.56
Node.js version: v20.19.2
npm version: 9.2.0
```

## RealSense Installed Files

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
/usr/local/lib/librealsense2-gl.so
/usr/local/lib/librealsense2-gl.so.2.56
/usr/local/lib/librealsense2.so
/usr/local/lib/librealsense2.so.2.56
```


## Known Notes

- `pyrealsense2` was found at:

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
```

- It may need to be copied into the current virtual environment:

```bash
cp -r /usr/local/lib/python3.13/dist-packages/pyrealsense2 \
  /home/matt/matt_drone/follow_project/.venv/lib/python3.13/site-packages/
```

- If pip fails with `No space left on device`, it may be because `/tmp` is small. Use:

```bash
mkdir -p ~/pip_tmp
TMPDIR=~/pip_tmp python -m pip install --no-cache-dir <package>
```
