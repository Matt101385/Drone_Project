# Depth-Aware Person-Following Drone

A PX4 person-following quadrotor using a Raspberry Pi 5, Hailo-10H person detection, Intel RealSense D435i depth, and MAVSDK Offboard control.

The Pi application converts target-distance and image-position guidance into local-NED `PositionNedYaw` setpoints. PX4 NED telemetry provides position feedback.

## Current Status

Working prototype. The main flight program is `src/follow_drone.py`; the Hailo detector wrapper is `src/hailo_person_detector.py`. Current target distance is 2.0 m. At follow entry the program captures the current N/E/D/yaw target. When visual guidance is lost, it latches the latest available N/E position once, retains the entry D target, and retains the previous yaw target.

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
.github/workflows/       Non-flight CI checks
~~~

The current detector resolves the Hailo `.hef` model from the Pi/Hailo environment; model assets for older MobileNet/TFLite/PyTorch paths have been removed from `main`.

## Run

The program defaults to dry mode:

~~~bash
FOLLOW_REAL=0 python3 src/follow_drone.py
~~~

Real control requires staged testing, RC takeover readiness, and a matching TELEM2 baud. The code default is `serial:///dev/serial0:921600`; the PX4 reference records `57600` from an earlier setup. Confirm the actual setting on the vehicle. The program requests Offboard automatically after connecting and obtaining a pose; it has no separate operator confirmation at that point.

~~~bash
FOLLOW_REAL=1 python3 src/follow_drone.py
~~~

WebRTC monitoring and target selection: `http://<raspberry-pi-ip>:8080`.

## Current Control Settings

| Setting | Main-program value |
| --- | ---: |
| Target distance | 2.0 m |
| Distance deadband | ±0.30 m |
| Displayed forward guidance | Clamped to ±0.8 m/s; it is not used as a flight-speed limit |
| Maximum yaw visual guidance | ±30 deg/s, converted to bounded yaw guidance |
| Position setpoint rate | 10 Hz |
| Horizontal position target offset | At most 1.00 m from the latest position reading |
| Yaw leash | ±30° |
| Down target | Captured NED Down value held |

## Safety and Limitations

This is experimental autonomous-flight software. Follow the [field-test checklist](docs/field_ops/field_test_checklist.md), verify RC override and vehicle health, test in a controlled area with an observer, and comply with applicable rules.

Current limitations include no obstacle avoidance, persistent person re-identification, global path planning, automatic takeoff/landing in the follow program, or authentication on the WebRTC interface. PX4 EKF Range Finder is not an obstacle-avoidance feature. Target continuity may fail when people cross or move close together. Position and yaw freshness are not continuously checked during follow, and an unmatched target-selection click remains pending. The current code needs these behaviors reviewed and validated before real follow.

## History and References

Historical prototypes and development notes are preserved on the [`archive-history` branch](https://github.com/Matt101385/Drone_Project/tree/archive-history/archive); they are not part of the default `main` view or current runtime. Current hardware/software facts are indexed in [docs/reference/](docs/reference/).

## Author and Disclaimer

**Muxi Zhang**

Educational and research use only. Autonomous aircraft testing carries substantial safety and regulatory risks; users are responsible for safe operation.
