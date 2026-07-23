# Historical SITL UDP Closed-Loop Validation

> **Status:** Historical validation record  
> **Architecture:** Pi vision → UDP → Mac receiver → PX4 SITL  
> **Current use:** This is not the startup procedure for the final v1.0 system.  
> **Purpose:** Preserved as evidence that the vision-to-flight-command chain was validated in simulation before real-flight integration.

This document records the current simulation test flow for the person-following
pipeline:

```text
Pi vision -> UDP JSON -> Mac receiver -> safety_supervisor -> PX4 SITL Offboard
```

This is a simulation validation workflow. It is not the final outdoor real-flight
startup procedure.

## Current Status

- Pi vision can detect and lock a person.
- Pi can send follow commands to the Mac over UDP.
- The Mac receiver can receive commands and pass them through `safety_supervisor.py`.
- PX4 SITL can arm, take off, enter Offboard, and receive velocity commands.
- This has not cleared the project for outdoor real-flight testing.

## Mac Terminal 1: Start PX4 SITL and Gazebo

Run this on the Mac:

```bash
cd ~/PX4-Autopilot
conda deactivate 2>/dev/null || true
export PATH="$(brew --prefix qt@5)/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/bin:/bin"
export CMAKE_PREFIX_PATH="$(brew --prefix qt@5):$(brew --prefix gz-gui8):$(brew --prefix gz-sim8)"
export Qt5_DIR="$(brew --prefix qt@5)/lib/cmake/Qt5"
source .venv/bin/activate
make px4_sitl gz_x500
```

QGroundControl can be opened separately to watch vehicle state, flight mode,
ground speed, heading, and the map position.

```bash
open -a QGroundControl
```

## Mac Terminal 2: Start the UDP Receiver in SITL Mode

Run this on the Mac after PX4 SITL is running:

```bash
cd /Users/matt/PX4-Autopilot
source .venv/bin/activate
python -u "/Users/matt/Documents/New project/tools/sim_follow_receiver.py" \
  --listen-host 0.0.0.0 \
  --listen-port 5005 \
  --sitl \
  --arm-and-takeoff
```

The `--sitl --arm-and-takeoff` flags are required for this test. Without them,
the receiver only prints UDP commands and does not control PX4.

Expected receiver output after success:

```text
[PX4] connected
[PX4] offboard active; UDP commands now drive SITL
[SAFETY] raw=(...) -> clamped=(...)
[PX4] sent locked=True ...
```

## Pi Terminal: Start the Vision UDP Test

Run this over SSH on the Pi:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python -u 10_webrtc_follow_udp_test.py
```

Expected Mac receiver output when the Pi is sending commands:

```text
[UDP] 10.0.0.105:... -> locked=True forward=... right=... down=... yaw=... source=pi-vision-10
[PX4] sent locked=True forward=... right=... down=... yaw=... source=pi-vision-10
```

If the receiver prints only `[DRY]`, it is not controlling PX4. Restart it with
`--sitl --arm-and-takeoff`.

## First Validation: Mac Local Fake Commands

Before using Pi vision, verify that the Mac receiver can move the PX4 SITL
vehicle using local UDP commands.

Forward test, sends a visible forward command for about 8 seconds:

```bash
python3 -c 'import json,socket,time; sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); payload={"forward_m_s":1.0,"right_m_s":0.0,"down_m_s":0.0,"yaw_deg_s":0.0,"target_locked":True,"source":"mac-big-forward-test"}; [(sock.sendto(json.dumps(dict(payload,sent_at=time.time())).encode(),("127.0.0.1",5005)), time.sleep(0.1)) for _ in range(80)]'
```

Yaw test, sends a visible yaw command for about 8 seconds:

```bash
python3 -c 'import json,socket,time; sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); payload={"forward_m_s":0.0,"right_m_s":0.0,"down_m_s":0.0,"yaw_deg_s":30.0,"target_locked":True,"source":"mac-big-yaw-test"}; [(sock.sendto(json.dumps(dict(payload,sent_at=time.time())).encode(),("127.0.0.1",5005)), time.sleep(0.1)) for _ in range(80)]'
```

Expected receiver output:

```text
[UDP] 127.0.0.1:... -> locked=True forward=+1.00 ...
[SAFETY] raw=(1.00, 0.00, 0.00, 0.00) -> clamped=(0.80, 0.00, 0.00, 0.00)
[PX4] sent locked=True forward=+1.00 ...
```

or for yaw:

```text
[UDP] 127.0.0.1:... -> locked=True ... yaw=+30.0
[SAFETY] raw=(0.00, 0.00, 0.00, 30.00) -> clamped=(0.00, 0.00, 0.00, 30.00)
[PX4] sent locked=True ... yaw=+30.0
```

## How to Confirm Movement

Use QGroundControl:

- Flight mode should stay in `OFFBOARD`.
- Ground speed should increase during forward tests.
- Heading should change during yaw tests.
- The vehicle marker should move on the map.

Use the PX4 SITL shell:

```bash
listener vehicle_local_position -n 5
```

Movement is confirmed if `x`, `y`, `vx`, `vy`, or `heading` changes while
commands are being sent.

## Notes From Current Testing

- `forward=-0.15` means the vehicle is moving backward slowly to increase
  distance from the person.
- `0.15 m/s` is visually subtle in Gazebo, so larger fake commands are useful
  for validating the Mac-to-PX4 path.
- The current Pi yaw preview value is too small if sent directly as `yaw_deg_s`.
  A value like `0.12` means only `0.12 deg/s`, which is almost invisible.
- For visible yaw in SITL, use a real degree-per-second command such as
  `10-30 deg/s`.

## Safety Gate

This workflow confirms the simulation closed loop only. Do not use it as
clearance for outdoor real-flight following.

Required next step before outdoor flight:

```text
No-prop real vehicle test:
Pi vision -> UDP/follow command -> safety supervisor -> Pixhawk command output
with props removed, RC override verified, command timeout verified, and mode
switch/kill behavior verified.
```
