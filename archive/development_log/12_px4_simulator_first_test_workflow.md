# 12 PX4 Simulator First Test Workflow

## Purpose

Record the first PX4 SITL / Gazebo / QGroundControl workflow.

## Two Test Lines

Real hardware line:

```text
Pi <-> PX4
```

Simulation line:

```text
Mac -> PX4 SITL -> Gazebo -> QGroundControl
```

## What to Check

- Gazebo opens with a simulated quadrotor.
- QGroundControl shows a connected simulated vehicle.
- PX4 terminal shows simulator and vehicle state output.

## Python Control Goal

The Python script should be able to:

- Connect.
- Arm.
- Take off.
- Start offboard mode.
- Send a small movement command.
- Stop.
- Land.

## Key Takeaway

Simulation is the safe place to develop offboard-control and safety logic before real-aircraft testing.
