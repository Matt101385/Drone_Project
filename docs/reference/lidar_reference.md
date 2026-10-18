# LiDAR Reference

## Reported Hardware

The project owner reports that a LiDAR has been added to the aircraft. These details have not yet been confirmed:

| Field | Status |
| --- | --- |
| Manufacturer and model | To be recorded |
| Interface and data protocol | To be recorded |
| Power source and voltage | To be recorded |
| Mounting position and orientation | To be recorded |
| Intended role | To be confirmed |

## Current Status

The owner reports that PX4 EKF is configured to use `Range Finder`. This records the reported PX4-side rangefinder/estimation configuration; the exact parameter ID/value, firmware version, and sensor status still need to be verified and captured in QGroundControl.

The Raspberry Pi companion program `src/follow_drone.py` does not initialize a LiDAR driver or read the LiDAR stream. It uses RealSense depth for person-distance guidance and receives PX4 NED telemetry for position feedback. The EKF setting is not obstacle avoidance, and the follow program has no LiDAR-based obstacle-avoidance logic.

Before relying on rangefinder data for height estimation, verify the sensor is detected and healthy in PX4/QGroundControl and confirm the parameter on the actual vehicle.

## Details To Record

- Manufacturer, exact model, and firmware.
- Electrical interface, connector/pinout, protocol, baud/data rate.
- Power requirements/source; mount, orientation, field of view, aircraft mass impact.
- Intended function: ranging, altitude sensing, obstacle detection, or another purpose.
- Driver/library and runtime configuration after integration.