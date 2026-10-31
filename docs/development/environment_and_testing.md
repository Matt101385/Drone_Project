# Development Environment and Verification

## Runtime Environment

The project targets the Raspberry Pi 5 environment recorded in [the Pi reference](../reference/pi5_environment_reference.md). Runtime dependencies span Python packages (including NumPy, OpenCV, RealSense Python bindings, aiohttp/aiortc/av, MAVSDK, and Hailo application modules) plus system/vendor components for librealsense and Hailo. A generic desktop `pip install` is not a substitute for the Pi/Hailo setup.

No version-locked dependency file is currently published. Exact versions must be captured from the working Pi before creating a lock file; do not guess package versions or upgrade the flight computer as part of documentation cleanup.

With the active Pi virtual environment enabled, record Python packages using:

```bash
python --version
python -m pip freeze --all
```

Also record Raspberry Pi OS, Hailo runtime/software and HEF model, RealSense firmware/library, PX4 firmware, and TELEM2 settings. Review local paths and secrets before committing any environment export.

## Verification

The field checklist describes staged dry and hardware checks. The previously referenced hover-test utility is absent from `main`, so a verified takeoff/hover/landing procedure must be established separately. The repository currently has no isolated control-logic test suite; syntax checks do not verify Offboard behavior or flight safety.

A lightweight CI job compiles the Python sources without importing hardware libraries or connecting to PX4. It catches syntax errors only; hardware testing remains manual and staged.