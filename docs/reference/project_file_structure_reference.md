# Project File Structure Reference

## Active Project

Current Raspberry Pi project path:

```text
~/matt_drone/follow_project
```

GitHub repository:

```text
Matt101385/Drone_Project
```

## Main Runtime Files

| File | Role |
| --- | --- |
| `scripts/11_follow_safe.py` | Current RealSense + YOLO + WebRTC + safety follow program. |
| `scripts/safety_supervisor_v2.py` | Safety layer for Offboard velocity commands. |
| `scripts/13_takeoff_hover_land_test.py` | PX4 takeoff, hover, and land smoke test. |
| `scripts/10_webrtc_follow_udp_test.py` | Intermediate WebRTC/UDP validation script. |
| `realsense_depth.py` | Small RealSense depth test/helper script. |
| `stream_mjpeg.py` | Older basic MJPEG stream script. |

## Reference Docs

| File | Role |
| --- | --- |
| `docs/reference/README.md` | Reference folder index. |
| `docs/reference/current_startup_workflow.md` | Current startup commands. |
| `docs/reference/pi5_environment_reference.md` | Pi 5 OS, Python, and environment facts. |
| `docs/reference/pixhawk_px4_reference.md` | Pixhawk/PX4 wiring and flight-mode reference. |
| `docs/reference/realsense_d435i_reference.md` | RealSense D435i device and runtime facts. |
| `docs/reference/project_file_structure_reference.md` | This file. |

## Field Docs

```text
docs/field_ops/field_test_checklist.md
docs/testing/sitl_follow_closed_loop_test.md
```

## Do Not Commit Runtime Files

```text
__pycache__/
logs/
.venv/
.env
*.log
*.backup*
*.broken_backup*
*.before_transfer*
color.jpg
depth.jpg
realsense_color.jpg
realsense_depth.jpg
```

## Still To Confirm For Final Report

- Frame model and wheelbase.
- Motor model and KV rating.
- ESC model and current rating.
- Propeller size.
- Battery capacity, C rating, and weight.
- GPS module model.
- RC receiver model.
- Power module or BEC model.
- Full takeoff weight.
