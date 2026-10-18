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

## Current Software Status

The current `src/follow_drone.py` does not initialize a LiDAR driver or read a LiDAR stream. Target-distance guidance uses Intel RealSense D435i depth, and position feedback comes from PX4 NED telemetry. LiDAR is not currently part of the follow-control or obstacle-avoidance path.

Do not treat the installed LiDAR as an active safety feature until its model/interface are identified, integration is implemented, and behavior is tested safely on the bench and in staged tests.

## Details To Record

- Manufacturer, exact model, and firmware.
- Electrical interface, connector/pinout, protocol, baud/data rate.
- Power requirements/source; mount, orientation, field of view, aircraft mass impact.
- Intended function: ranging, altitude sensing, obstacle detection, or another purpose.
- Driver/library and runtime configuration after integration.