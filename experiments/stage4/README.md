# Stage 4 matched-control pair — DRAFT / SITL only

**Status: source-level preparation only. NOT flight-tested.**
This branch does not change main/src/follow_drone.py and does not restore the old Safety Supervisor.

## Why these files exist

For a scientific comparison, the historical Velocity program and the current Position program must not be compared naively: old Velocity had 4.0 m follow distance, raw depth-based distance, no current tilt/pitch correction or distance-rate braking; Position has 2.0 m target distance, current RealSense geometry and filter. The historical versions are preserved in Git: Velocity `06168f93cb91db6e25a63ac87fbaee871defb113`; Position `da2b9d9b6ae37cf96dd6b2ec73716866a2ca604f`.

The matched pair is **generated from the exact same Position-version source**, Git blob `d25d53232871d6a22f26834fcf5f2837466d2289`, rather than from two different historical vision pipelines. They differ at source level only by `STAGE4_CONTROL_MODE`:

- `position_matched.py`: the common moving N/E/D/Yaw target is sent to PX4 as `PositionNedYaw`. PX4 performs its native position->velocity conversion.
- `velocity_matched.py`: the **same** common moving N/E/D/Yaw target and the **same PX4 estimated pose** are used by a companion-side proportional conversion to body-forward/right/down velocities plus yaw rate, sent through `VelocityBodyYawspeed`.

This specifically compares the **placement of the position-error-to-velocity outer loop**, not original August Velocity versus today's entire codebase. The matched Velocity branch is a new research comparator, not a claim that these lines were flown in August.

## Shared variables

Both source files (by construction): `TARGET_DIST_M=2.0`, `CONF_THRES=0.25`, `DEPTH_MAX_M=10.0`, `DEADBAND=0.06`, `DIST_DEADBAND=0.30`, `Kp=20`, `Kp_forward=0.65`, `MAX_FORWARD_CMD=0.8` (displayed guidance only in Position), `CAMERA_TILT_DEG=30`, `DIST_RATE_KD_S=0.35`, `DIST_RATE_FILTER_ALPHA=0.20`, `DIST_RATE_DEADBAND_M_S=0.10`, `POSITION_SETPOINT_HZ=10`, same YOLO/Hailo detector, same RealSense distance/deprojection, target selection, target-loss logic, WebRTC interface and shared NED target generation.

Both launch copies use the same source-level setpoint sender, initial N/E/D/Yaw sampling, 1.5 s prestream, and manual mode-exit handler. The old standalone Safety Supervisor is **not** included.

Velocity-only conversion parameters are `STAGE4_KP_XY_S=0.65`, `STAGE4_KP_Z_S=0.50`, `STAGE4_KP_YAW_S=1.0`, and max body XY speed 0.80 m/s, max down speed 0.20 m/s and max yaw rate 30 deg/s. **These values are provisional and must be calibrated/prespecified with actual PX4 MPC gains and attained speeds before formal trials.** There is no direct numerical equivalence between position-offset meters and velocity m/s.

## Safety and prerequisites

The experimental programs reject any non-`udp://` MAVSDK connection or absent `STAGE4_SITL_ACK=SIM_ONLY` in active control mode. These are **not** for real flight.

These scripts still access **physical RealSense/Hailo** from the Pi-oriented source. They are **not yet directly runnable for Gazebo person-following on a desktop**; the simulated RGB/depth-to-vision bridge and detector adapter must be integrated and tested separately. Do not equate Python syntax checks with SITL success.

For the source contract/syntax smoke test (no flight, no hardware imports):

```bash
python3 experiments/stage4/test_matched_source.py
```

When the external Gazebo camera/perception bridge and safe PX4 SITL are actually ready, test one at a time from repository root with `PYTHONPATH=src`; explicitly configure the correct SITL URL and environment. Example (do not run against hardware):

```bash
PYTHONPATH=src FOLLOW_REAL=1 STAGE4_SITL_ACK=SIM_ONLY PX4_ADDR=udp://:14540 \
  python3 experiments/stage4/position_matched.py
```

## Formal A/B/C/D configuration

A=matched Velocity + barometer-height profile; B=matched Position + barometer-height profile; C=matched Velocity + validated PX4 EKF rangefinder profile; D=matched Position + the same rangefinder profile. Run the **same prerecorded Gazebo actor path**, initial aircraft condition, model, estimator parameter profile (within each LiDAR pair) and sensor/noise settings. Verify PX4 rangefinder fusion in logs. Compare actual height RMSE, p-p range, XY path tracking, measured speed, setpoint timing and ground truth, with matched run durations.

**Unresolved:** Compensating for materially different attained XY speeds; PX4 MPC gains, exact EKF configs, simulated rangefinder fusion, independent truth and complete run logs. Do not claim causal isolation until these are validated.
