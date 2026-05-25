# Project File Structure Reference

Last updated: 2026-05-16

## Purpose

This document explains how the drone project files are currently organized on the Raspberry Pi 5 and how the main folders should be treated.

## Current Top-Level Local Layout

Current working folder group:

```text
~/matt_drone/
  follow_project/          # Python / RealSense / YOLO / drone vision project
  my-app/                  # Next.js dashboard prototype
```

Cleanup backup folder:

```text
~/matt_drone_cleanup_backup/
```

The backup folder contains old duplicate project copies and temporary files moved out during cleanup. Do not use it as the active project location unless intentionally recovering an old file.

## Main Python Project

Current active Python vision project:

```text
~/matt_drone/follow_project
```

This is the main project that is currently synced with GitHub:

```text
Matt101385/Drone_Project
```

The project root should stay focused on the current runtime program, required support modules, models, reference docs, and historical archives.

Recommended structure:

```text
follow_project/
  scripts/07_latest_yolo_person_follow_click_target_stream.py
  scripts/realsense_reader_module.py
  models/
  docs/
  archive/
  .gitignore
  .gitattributes
```

## Current Main Program

```text
scripts/07_latest_yolo_person_follow_click_target_stream.py
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
- Browser video stream backend.

## Support Module

```text
scripts/realsense_reader_module.py
```

Purpose:

- Reusable RealSense reader logic.
- Camera restart / recovery support.
- Frame locking and safe frame access.

## Models

Important model files may appear in the project root or inside `models/`, depending on the script history. The preferred direction is to keep model assets in `models/` when practical.

Current primary YOLO model:

```text
yolo11n.pt
models/yolo11n.pt
```

`yolo11n.pt` is the model to keep for the current GitHub showcase version.

Removed from GitHub showcase:

```text
yolov8n.pt
models/yolov8n.pt
```

`yolov8n.pt` was an older YOLO model used for comparison/history. It should not be treated as a required GitHub project file. If needed, keep it only as a local backup outside the showcase path.

Legacy experiment model files:

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

## Dashboard Website Project

Current local dashboard project:

```text
~/matt_drone/my-app
```

Purpose:

- Next.js web dashboard prototype.
- Display RealSense/YOLO stream through a browser UI.
- Send click-target requests from the browser to the Python backend.
- Show Pi/system status cards.

Important files:

```text
my-app/
  app/page.tsx
  app/StreamViewer.tsx
  app/api/realsense/route.ts
  app/api/realsense/select-target/route.ts
  system.ts
  package.json
  package-lock.json
  .gitignore
```

Current package script rule:

```text
npm run dev         # website only
npm run dev:web     # website only
npm run dev:camera  # Python camera backend only
npm run dev:all     # website + Python camera backend
```

Current backend target used by `npm run dev:camera`:

```text
/home/matt/matt_drone/follow_project/.venv/bin/python /home/matt/matt_drone/follow_project/scripts/07_latest_yolo_person_follow_click_target_stream.py
```

Important Git rule:

```text
Do not push from ~/matt_drone/my-app yet.
```

Reason: `my-app` is currently a separate local Git repository, but it points to the same GitHub repo as `follow_project`. Publishing it should wait until the GitHub repository structure is intentionally reorganized.

## Reference Documentation

Current reference docs live in:

```text
~/matt_drone/follow_project/docs/reference/
```

Important files:

```text
docs/reference/current_startup_workflow.md
docs/reference/pi5_environment_reference.md
docs/reference/project_file_structure_reference.md
docs/reference/realsense_d435i_reference.md
docs/reference/pixhawk_px4_reference.md
```

Reference docs are for current working facts. If startup commands, project paths, hardware settings, or package versions change, update the relevant reference file after Matt approves the GitHub update.

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

Historical notes should stay in:

```text
docs/project_notes/
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

Website runtime/build files should also stay out of GitHub:

```text
my-app/.next/
my-app/node_modules/
my-app/*.pt
my-app/*.onnx
my-app/*.tflite
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

If a file is needed to run the latest Python program, keep it in `follow_project/` or `follow_project/models/`.

If a file belongs to the dashboard prototype, keep it in `my-app/`.

If a file is only useful for history, move it to `archive/experiments/` or `docs/project_notes/`.

If a file is generated at runtime, ignore it.

If a file is an old duplicate from before cleanup, keep it in `~/matt_drone_cleanup_backup/` unless intentionally restoring it.

## Future Repository Direction

The likely clean long-term GitHub structure is:

```text
Drone_Project/
  follow_project/
  my-app/
  docs/
```

This reorganization has not been done yet. Until it is done, treat `follow_project` as the main GitHub-synced project and keep `my-app` local.
