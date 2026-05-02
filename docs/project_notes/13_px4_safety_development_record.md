# 13 PX4 Safety Development Record

## Purpose

Record development of a reusable safety layer for PX4 offboard-control programs.

## Current Stage

Working:

- Pi to PX4 serial link through TELEM2.
- PX4 SITL + Gazebo + QGroundControl.
- Python can connect, arm, take off, move, stop, and land in simulation.

## Core Goal

Build safety that is reusable across future scripts:

- Simple forward flight.
- Person following.
- Vision-guided motion.
- Future offboard-control programs.

## Development Path

1. Minimum offboard flight test.
2. Roll/pitch attitude failsafe.
3. Command limiting before sending unsafe commands.
4. Reusable safety layer independent of task logic.
5. Manual override priority: if PX4 leaves OFFBOARD, program stops.
6. Interruptible waits so background watchdogs can stop the main flow.

## Safety Model

Layer 1: command limiting.

```text
forward max: 0.8 m/s
right max:   0.8 m/s
down max:    0.5 m/s
yaw max:     30 deg/s
```

Layer 2: program supervisor.

- Roll / pitch.
- Command timeout.
- Target lost.
- Manual takeover.
- Later: altitude, velocity, link state.

Layer 3: PX4 system failsafes.

- Offboard loss.
- RC override.
- GPS / estimator issues.
- Battery.
- Geofence.
- Return / land.

## Key Takeaway

Safety should be a reusable layer between task logic and PX4 commands, not a patch added after the task works.
