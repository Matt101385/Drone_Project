# 01 Project Start: Vision, RealSense, and MJPEG Streaming

## Purpose

Record the starting point of the visual-following drone project using Raspberry Pi, Pixhawk 6X, and Intel RealSense D435i.

## Initial Goal

At this stage the project focused only on vision:

- Capture camera frames.
- Verify visual recognition.
- Display the image stream.
- Avoid flight-control integration for now.

## Initial System State

- Raspberry Pi with Python 3.13 and virtual environment.
- Pixhawk MAVLink heartbeat already verified.
- RealSense D435i detected over USB.
- `realsense-viewer` working.
- `pyrealsense2` import working.

## Key Progress

The early `cv2.imshow()` approach failed because the Pi was used headlessly over SSH. This was not a camera problem.

The correct engineering solution was MJPEG streaming:

```text
RealSense -> OpenCV -> JPEG encode -> Flask stream -> browser display
```

Important early scripts:

```text
rs_save_test.py
stream_mjpeg.py
stream_face_mjpeg.py
```

## Recognition Attempts

Face detection with OpenCV Haar Cascade worked and produced useful `dx` / `dy` target offset values.

Person detection had several explored paths:

- HOG person detector: unreliable indoors.
- MobileNet SSD: blocked by model-file download issues.
- Early YOLO: initially blocked by Python / PyTorch / ARM compatibility.

## Key Takeaway

The foundation was proven:

```text
RealSense camera -> Python vision processing -> browser stream -> target offset data
```
