# 07 Pi 5 Migration, RealSense, YOLO, and AI HAT Debugging

## Purpose

Record the migration from Pi 4 to Pi 5 and debugging around RealSense, YOLO streaming, and the AI HAT.

## Migration Goal

Restore:

- RealSense camera access.
- YOLO stream.
- Web display.

## AI HAT Checks

Checked:

- PCIe detection.
- Hailo device.
- `/dev/hailo0`.
- Kernel driver.
- Firmware.
- Python runtime.
- Model files.

Conclusion: the HAT was detected, but official examples were not the fastest path.

## Main Code Repair

Main file:

```text
stream_mjpeg_yolo.py
```

Important fixes:

- Separate camera capture errors from YOLO processing errors.
- Avoid unnecessary RealSense restarts.
- Fix indentation and old copy-paste structure issues.
- Standardize on `color_image`.
- Restore click-target selection.
- Compile repeatedly with `python -m py_compile`.

## Final Observation

Logs showed frames were actually arriving:

```text
got frames
color_frame ok: True
color_image shape: (480, 640, 3)
```

## Key Takeaway

Camera and Pi 5 hardware were mostly fine. The remaining work was code cleanup and process management.
