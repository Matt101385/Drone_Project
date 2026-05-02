# Project File Structure Reference

## Purpose

This document explains how the `follow_project` files should be organized.

## Recommended Root Structure

The project root should stay focused on the current runtime program and required assets.

```text
follow_project/
  07_latest_yolo_person_follow_click_target_stream.py
  realsense_reader_module.py
  yolo11n.pt
  yolov8n.pt
  models/
  archive/
  .gitignore
  .gitattributes
```

## Current Main Program

```text
07_latest_yolo_person_follow_click_target_stream.py
```

Original historical name:

```text
stream_mjpeg_yolo.py
```

Purpose:

- RealSense color/depth stream.
- YOLO person detection.
- Click-to-select target.
- Target lock.
- Distance reading.
- Yaw / forward command preview.
- Flask MJPEG stream.

## Support Module

```text
realsense_reader_module.py
```

Purpose:

- Reusable RealSense reader logic.
- Camera restart / recovery support.
- Frame locking and safe frame access.

## Models

Important files:

```text
yolo11n.pt
```

Current main YOLO model used by the latest program.

```text
yolov8n.pt
```

Older YOLO model kept for comparison / history.

```text
models/detect.tflite
models/labelmap.txt
```

TFLite experiment model and labels.

```text
models/MobileNetSSD_deploy.caffemodel
models/MobileNetSSD_deploy.prototxt
```

MobileNet SSD experiment files.

## Archive

Experiment scripts should be stored in:

```text
archive/experiments/
```

These files are not the current runtime program. They exist for history and project summaries.

Examples:

```text
01_realsense_capture_save_test.py
02_realsense_basic_mjpeg_stream.py
03_face_detection_mjpeg_stream.py
04_realsense_depth_center_distance_test.py
04a_failed_hog_person_detection_stream.py
04b_failed_mobilenet_ssd_person_detection_stream.py
05_tflite_legacy_proxy_detection_stream.py
06_tflite_integrated_object_detection_stream.py
06a_early_yolov8_person_detection_stream.py
```

## Runtime Files Not to Track

Do not keep these in GitHub:

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

## Git LFS

Large model files such as `.pt`, `.tflite`, and `.zip` may need Git LFS.

Expected tracked patterns:

```text
*.pt
*.zip
*.tflite
```

## Cleanup Rule

If a file is needed to run the latest program, keep it in the root or `models/`.

If a file is only useful for history, move it to `archive/experiments/`.

If a file is generated at runtime, ignore it.
