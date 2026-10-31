# Recovered Pre-Cleanup Snapshot

These distinct historical files were recovered from commit `ea9a8cd` after an archive cleanup. Paths and instructions within them describe that earlier snapshot and may no longer work. They are preserved for reference and are not current flight procedures.

- `src/follow_drone.py` and `scripts/11_follow_safe.py` are older, different program versions.
- `scripts/safety_supervisor_v2.py` is retained once; the former `src` copy was byte-identical.
- `tests/hardware/takeoff_hover_land_test.py` is an old flight-test utility, not validated for the current vehicle. The earlier numbered copy differed only in its example command text.
- The former development-note copies were byte-identical to `archive/development_log/`; the old SITL document differed from the retained validation record only in its heading and historical notice.
- The `.pt`, `.zip`, and `.tflite` entries are Git LFS pointers in the recovered commit. Actual model payload availability has not been checked. `models/download_error.html` preserves one copy of an HTML error page that had been saved under both MobileNet model filenames; it is not a model.
