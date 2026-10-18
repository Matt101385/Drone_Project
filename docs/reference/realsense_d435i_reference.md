# RealSense D435i Reference

## Current Role

The Intel RealSense D435i provides the vision input for the follow-drone system:

- Color stream for YOLO person detection.
- Depth stream for target-distance estimation.
- Browser video stream for target selection and monitoring.

## Confirmed Device Data

Collected from `lsusb` on the Raspberry Pi 5.

| Field | Value |
| --- | --- |
| Device | Intel RealSense Depth Camera 435i |
| USB vendor/product ID | `8086:0b3a` |
| USB bus | Bus 002 |
| USB device | Device 002 |
| USB root hub | Linux Foundation 3.0 root hub |

Raw `lsusb` line:

```text
Bus 002 Device 002: ID 8086:0b3a Intel Corp. Intel(R) RealSense(TM) Depth Camera 435i
```

## Runtime Settings

Current main program settings:

| Setting | Value |
| --- | --- |
| Color stream | 640 x 480 |
| Depth stream | 640 x 480 |
| FPS | 30 |
| Color format | `bgr8` |
| Depth format | `z16` |
| Minimum valid depth | 0.3 m |
| Maximum valid depth | 10.0 m |
| Target follow distance | 2.0 m |

The main program currently uses RealSense depth for target-distance estimation. The reported LiDAR is not read by the main program; see [LiDAR reference](lidar_reference.md).

## Python Check

From the active project environment:

```bash
cd ~/Drone_Project
source .venv/bin/activate
python -c "import pyrealsense2 as rs; print('realsense ok')"
```

Known system RealSense library files from earlier setup:

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
/usr/local/lib/librealsense2.so.2.56
/usr/local/lib/librealsense2-gl.so.2.56
```

## Still To Record

- RealSense serial number.
- RealSense firmware version.
- Exact pyrealsense2 build/version.
- Confirmed USB mode from RealSense API.
