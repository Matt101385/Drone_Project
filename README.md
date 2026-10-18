# Depth-Aware Person-Following Drone

A vision-based person-following quadrotor built with PX4, Raspberry Pi 5, Intel RealSense D435i, Hailo-10H person detection, and MAVSDK Offboard control.

The system detects people, allows an operator to select a target through a web interface, estimates target distance using RealSense depth, and converts bounded visual guidance into local-NED position/yaw setpoints.

## Project Status

**Version:** v1.0 baseline  
**Status:** Field-tested working prototype

## Project Status

**Status:** Working prototype; verify vehicle configuration and complete staged checks before real flight.

The current main program runs Hailo-10H person detection, operator target selection, RealSense depth estimation, PX4 NED position feedback, and `PositionNedYaw` setpoints. On follow entry it captures current position/yaw; without valid visual guidance it holds the last complete N/E/D/yaw target. The Down (altitude) target remains at its captured value.

The LiDAR is reported as installed, but its model/interface are not recorded and the current main program does not read its data. Do not rely on it for obstacle avoidance or flight control.

## System Architecture

~~~text
Intel RealSense D435i
        |
        v
Raspberry Pi 5
  - YOLO11n person detection
  - Click-to-select target
  - Depth-based distance estimation
  - Follow-command generation
  - WebRTC monitoring interface
  - Flight-data logging
        |
        v
MAVSDK / PX4 Offboard Control
        |
        v
Pixhawk 6X
        |
        v
Holybro X500 V2 Quadcopter
~~~

## Hardware Platform

- Holybro X500 V2 quadcopter platform
- Pixhawk 6X flight controller
- PX4 flight-control software
- Raspberry Pi 5 companion computer
- Intel RealSense D435i depth camera
- LiDAR (reported installed; model/interface and role to be recorded)
- Holybro M10 GPS
- 4S LiPo battery
- Serial connection from Raspberry Pi to Pixhawk TELEM2

Current hardware and environment information is stored in [`docs/reference/`](docs/reference/); see [`docs/reference/lidar_reference.md`](docs/reference/lidar_reference.md) for LiDAR status.

## Main Software

~~~text
src/
├── follow_drone.py             Main vision and position-follow runtime
└── hailo_person_detector.py    Hailo-10H detector
~~~

### `follow_drone.py`

`src/follow_drone.py` contains the follow controller and its prestream, telemetry, and manual-override handling; there is no separate `safety_supervisor_v2.py` module in this repository. This documentation update does not modify the main program.

## Repository Structure

~~~text
archive/                 Historical notes, prototypes, and validation material
docs/field_ops/          Field-test checklist
docs/reference/          Current hardware and software references
models/                  Model assets
src/                     Runtime software
tests/hardware/          Hardware flight-test utilities

## Running the Software

The application defaults to dry mode. It does not send real flight commands unless real control is explicitly enabled.

### Dry Mode

~~~bash
FOLLOW_REAL=0 python3 src/follow_drone.py
~~~

### Real PX4 Control

~~~bash
FOLLOW_REAL=1 python3 src/follow_drone.py
~~~

The default PX4 serial connection is:

~~~text
serial:///dev/serial0:921600 (code default; verify actual TELEM2 baud before real control)
~~~

The WebRTC monitoring and target-selection interface is available at:

~~~text
http://<raspberry-pi-ip>:8080
~~~

## Baseline Control Configuration

| Parameter | Baseline value |
| --- | ---: |
| Setting | Current main-program value |
| --- | ---: |
| Target following distance | 2.0 m |
| Distance deadband | ±0.30 m |
| Maximum forward visual guidance | 0.8 m/s (converted to bounded position guidance) |
| Maximum yaw visual guidance | ±30 deg/s (converted to bounded yaw guidance) |
| Position setpoint rate | 10 Hz |
| Horizontal position leash | 1.00 m |
| Yaw leash | ±30° |
| Down/altitude target | Hold captured NED Down target |

## Safety Notes

This repository contains experimental autonomous-flight software.

Before real flight:

- Complete dry-mode testing
- Verify RC override and flight-mode recovery
- Confirm Pixhawk, GPS, and TELEM2 communication
- Confirm motor and propeller direction
- Use an open and controlled test area
- Maintain a safety observer
- Keep the aircraft within visual line of sight
- Keep the web interface on a trusted local network
- Follow all applicable aviation regulations

## Known Limitations

The current v1.0 system does not include:

- LiDAR integration and obstacle avoidance
- Persistent person re-identification
- Reliable multi-person identity tracking
- Global path planning
- Automatic takeoff or landing in the main follow program
- Authentication for the WebRTC interface

Target continuity is based mainly on the proximity of detection boxes between consecutive frames. The tracker may switch targets when multiple people cross or move close together.

The current controller holds the Down target captured on follow entry; it does not provide LiDAR ranging or obstacle avoidance.

## Development History

Historical engineering notes and prototype programs are preserved in:

- [`archive/development_log/`](archive/development_log/)
- [`archive/experiments/`](archive/experiments/)

These files document the progression from basic RealSense capture and early object-detection methods to the final PX4-integrated person-following system.

## Future Work

Potential future directions include:

- Obstacle detection and avoidance
- Target re-identification
- Dynamic altitude selection
- Improved depth filtering
- Quantitative altitude and distance-error evaluation
- Target-loss recovery
- Path planning around obstacles
- Multi-sensor fusion

These items are planned research directions and are not part of the current v1.0 implementation.

## Author

**Muxi Zhang**

## Disclaimer

This repository is provided for educational and research purposes. Autonomous aircraft testing involves substantial safety and regulatory risks. Users are responsible for safe operation and compliance with all applicable laws, regulations, and operating requirements.
