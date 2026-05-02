# 08 Pi 5 Device Information and Environment Status

## Purpose

Record hardware and environment state after moving to Raspberry Pi 5.

## Hardware

- Raspberry Pi 5 became the main machine.
- Intel RealSense D435i was detected over USB.
- YOLO stream later ran successfully.

## Migrated Projects

Main AI/camera project:

```text
~/follow_project
```

Important files:

```text
stream_mjpeg_yolo.py
realsense_depth.py
rs_save_test.py
stream_face_mjpeg.py
stream_mjpeg_tflite.py
yolo11n.pt
yolov8n.pt
```

Website:

```text
~/my-app
```

Pixhawk test script:

```text
hello_pixhawk.py
```

## RealSense Environment

`pyrealsense2` location:

```text
/usr/local/lib/python3.13/dist-packages/pyrealsense2
```

RealSense libraries:

```text
/usr/local/lib/librealsense2.so.2.56
/usr/local/lib/librealsense2-gl.so.2.56
```

## Status

Working:

- RealSense software path.
- YOLO main program.
- Pi 5 performance improvement.

Remaining:

- Node/npm setup on Pi 5.
- Full website verification.
- Full Pixhawk integration test after migration.
