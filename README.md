# Depth-Aware Person-Following Drone

A PX4 person-following quadrotor using a Raspberry Pi 5, Hailo-10H person detection, Intel RealSense D435i depth, and MAVSDK Offboard control.

The Pi application converts target-distance and image-position guidance into local-NED `PositionNedYaw` setpoints. PX4 NED telemetry provides position feedback.

## Current Status

Working prototype. The main flight program is `src/follow_drone.py`; the Hailo detector wrapper is `src/hailo_person_detector.py`. Current target distance is 2.0 m. At follow entry the program captures the current N/E/D/yaw target; when valid visual guidance is absent, it holds the last complete target.

The owner reports PX4 EKF configured to use `Range Finder`. This is a PX4-side rangefinder/estimation setting; the Pi follow program does not read the LiDAR stream directly. It does not provide obstacle avoidance. Device details and the exact PX4 parameter are still being recorded in the [LiDAR reference](docs/reference/lidar_reference.md) and [PX4 reference](docs/reference/pixhawk_px4_reference.md).

## System Architecture

~~~text
RealSense D435i color/depth → Raspberry Pi 5 + Hailo-10H
                                    - person detection/selection
                                    - visual distance/yaw guidance
                                    - WebRTC monitoring
                                                |
                                                v
                                  MAVSDK Offboard / PX4
                                  NED feedback + PositionNedYaw
                                                |
                                                v
                                      Pixhawk 6X / X500 V2

LiDAR → PX4 EKF Range Finder (owner-reported; physical interface not yet documented)
~~~

## Hardware

- Holybro X500 V2 with Pixhawk 6X / PX4
- Raspberry Pi 5 with Hailo-10H AI HAT
- Intel RealSense D435i
- LiDAR (reported; see references for unconfirmed details)
- Holybro M10 GPS and 4S LiPo
- Pi-to-Pixhawk TELEM2 serial link

## Repository Layout

~~~text
docs/field_ops/          Field checklist
docs/reference/          Hardware and software references
docs/development/        Environment and verification notes
src/                     Current runtime
tests/hardware/          Hardware flight-test utility
.github/workflows/       Non-flight CI checks
~~~

The current detector resolves the Hailo `.hef` model from the Pi/Hailo environment; model assets for older MobileNet/TFLite/PyTorch paths have been removed from `main`.

## Run

The program defaults to dry mode:

~~~bash
FOLLOW_REAL=0 python3 src/follow_drone.py
~~~

Real control requires staged testing, RC takeover readiness, and a matching TELEM2 baud. The code default is `serial:///dev/serial0:921600`, while the PX4 reference and standalone hover-test command record `57600`. Resolve this against the vehicle before real follow; do not change either setting based only on this README.

~~~bash
FOLLOW_REAL=1 python3 src/follow_drone.py
~~~

WebRTC monitoring and target selection: `http://<raspberry-pi-ip>:8080`.

## Current Control Settings

| Setting | Main-program value |
| --- | ---: |
| Target distance | 2.0 m |
| Distance deadband | ±0.30 m |
| Maximum forward visual guidance | 0.8 m/s, converted to bounded position guidance |
| Maximum yaw visual guidance | ±30 deg/s, converted to bounded yaw guidance |
| Position setpoint rate | 10 Hz |
| Horizontal position leash | 1.00 m |
| Yaw leash | ±30° |
| Down target | Captured NED Down value held |

## Safety and Limitations

This is experimental autonomous-flight software. Follow the [field-test checklist](docs/field_ops/field_test_checklist.md), verify RC override and vehicle health, test in a controlled area with an observer, and comply with applicable rules.

Current limitations include no obstacle avoidance, persistent person re-identification, global path planning, automatic takeoff/landing in the follow program, or authentication on the WebRTC interface. PX4 EKF Range Finder is not an obstacle-avoidance feature. Target continuity may fail when people cross or move close together.

## History and References

Historical prototypes and development notes are preserved on the [`archive-history` branch](https://github.com/Matt101385/Drone_Project/tree/archive-history/archive); they are not part of the default `main` view or current runtime. Current hardware/software facts are indexed in [docs/reference/](docs/reference/).

## Author and Disclaimer

**Muxi Zhang**

Educational and research use only. Autonomous aircraft testing carries substantial safety and regulatory risks; users are responsible for safe operation.