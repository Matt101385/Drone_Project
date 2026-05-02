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
python 07_latest_yolo_person_follow_click_target_stream.py
```

## Current Version Fields

These values should be updated from the Pi 5 terminal.

```text
Raspberry Pi model: TODO
OS version: TODO
Kernel version: TODO
Python version: TODO
pip version: TODO
OpenCV version: TODO
Ultralytics version: TODO
Torch version: TODO
Torchvision version: TODO
RealSense Python binding: TODO
librealsense version/files: TODO
Node.js version: TODO
npm version: TODO
```

## Commands to Collect Version Information

Run this on the Pi 5 and paste the output into ChatGPT when this file needs to be updated:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate

printf '\n--- System ---\n'
cat /proc/device-tree/model 2>/dev/null || true
cat /etc/os-release
uname -a

printf '\n--- Python ---\n'
which python
python -V
python -m pip --version

printf '\n--- Python packages ---\n'
python - <<'PY'
mods = ['cv2', 'ultralytics', 'torch', 'torchvision', 'numpy', 'flask']
for m in mods:
    try:
        mod = __import__(m)
        print(f'{m}:', getattr(mod, '__version__', 'import ok'))
    except Exception as e:
        print(f'{m}: ERROR {e}')
try:
    import pyrealsense2 as rs
    print('pyrealsense2: import ok')
except Exception as e:
    print('pyrealsense2: ERROR', e)
PY

printf '\n--- RealSense files ---\n'
ls -l /usr/local/lib/python3.13/dist-packages | grep pyrealsense || true
ls -l /usr/local/lib | grep librealsense || true

printf '\n--- Node / npm ---\n'
node -v 2>/dev/null || true
npm -v 2>/dev/null || true
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
