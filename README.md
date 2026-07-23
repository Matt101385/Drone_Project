# Depth-Aware Person-Following Drone

A vision-based person-following quadrotor built with PX4, Raspberry Pi 5, Intel RealSense D435i, YOLO11n, and MAVSDK Offboard control.

The system detects people, allows an operator to select a target through a web interface, estimates the target distance using depth data, and generates bounded velocity and yaw commands for the flight controller.

## Project Status

**Version:** v1.0 baseline  
**Status:** Field-tested working prototype

The current system can:

- Detect people using YOLO11n
- Select a target by clicking the web video feed
- Track the selected target between consecutive frames
- Estimate target distance using RealSense depth data
- Maintain a target following distance
- Rotate the aircraft to keep the target near the image center
- Maintain approximately 1.5 m relative altitude
- Stop horizontal and yaw tracking when the target is lost
- Continue altitude hold after target loss
- Use a safety supervision layer for real PX4 commands
- Record flight telemetry and control commands in CSV logs
- Stream annotated video through WebRTC

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
- Holybro M10 GPS
- 4S LiPo battery
- Serial connection from Raspberry Pi to Pixhawk TELEM2

Current hardware and environment information is stored in [`docs/reference/`](docs/reference/).

## Main Software

~~~text
src/
├── follow_drone.py
└── safety_supervisor_v2.py
~~~

### `follow_drone.py`

The main runtime application provides:

- RealSense color and depth capture
- YOLO11n person detection
- Web-based target selection
- Target continuity between frames
- Depth-based following-distance control
- Image-based yaw alignment
- Fixed-altitude control
- WebRTC video streaming
- PX4 Offboard command output
- Flight CSV logging

### `safety_supervisor_v2.py`

The safety supervision layer supports:

- Command monitoring
- Velocity and acceleration limits
- Roll and pitch monitoring
- Offboard failsafe behavior
- Zero-command cleanup during shutdown

## Repository Structure

~~~text
archive/
├── development_log/   Historical engineering notes
└── experiments/       Early prototypes and failed approaches

docs/
├── field_ops/         Field-test checklist
├── reference/         Current hardware and software references
└── testing/           SITL and closed-loop test documentation

models/                Legacy object-detection models
src/                   Current runtime software
tests/hardware/        Hardware flight-test utilities
yolo11n.pt              YOLO11n weights managed with Git LFS
~~~

## Running the Software

The application defaults to dry mode. It does not send real flight commands unless real control is explicitly enabled.

### Dry Mode

~~~bash
FOLLOW_REAL=0 python3 src/follow_drone.py
~~~

### Real PX4 Control

~~~bash
FOLLOW_REAL=1 FOLLOW_ALT_M=1.5 python3 src/follow_drone.py
~~~

The default PX4 serial connection is:

~~~text
serial:///dev/serial0:57600
~~~

The WebRTC monitoring and target-selection interface is available at:

~~~text
http://<raspberry-pi-ip>:8080
~~~

## Baseline Control Configuration

| Parameter | Baseline value |
| --- | ---: |
| Target following distance | 4.0 m |
| Distance deadband | ±0.30 m |
| Target altitude | 1.5 m |
| Altitude deadband | ±0.10 m |
| Maximum forward speed | 0.8 m/s |
| Maximum vertical speed | 0.2 m/s |
| Maximum yaw rate | 30 deg/s |
| Command frequency | 10 Hz |

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

- Obstacle avoidance
- Persistent person re-identification
- Reliable multi-person identity tracking
- Horizontal position hold
- Global path planning
- Automatic takeoff or landing in the main follow program
- Authentication for the WebRTC interface

Target continuity is based mainly on the proximity of detection boxes between consecutive frames. The tracker may switch targets when multiple people cross or move close together.

The altitude controller maintains a fixed relative-altitude target rather than recording the altitude automatically when Offboard mode begins.

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
