# Scripts

This folder holds runnable Python programs and support modules that are still part of the current project line.

## Current / Maintained

- `07_latest_yolo_person_follow_click_target_stream.py` - validated MJPEG RealSense + YOLO click-target stream.
- `12_takeoff_hover_land_test.py` - conservative PX4 takeoff, hover, and land smoke test.
- `safety_supervisor_v2.py` - safety gate for real follow velocity commands.
- `realsense_reader_module.py` - reusable RealSense reader/recovery helper.

## To Add From Pi

These should be copied from the Pi when the current real versions are ready:

- `10_webrtc_follow_udp_test.py`
- `11_follow_safe.py`

Keep old experiments in `archive/experiments/`, not here.
