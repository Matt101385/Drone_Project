# Field Test Checklist

This checklist is for the Pi + Pixhawk + RealSense follow project.

## Operating Modes

Use home or phone Wi-Fi while developing:

```bash
ssh matt@10.0.0.105
```

Use the Pi hotspot only in the field:

```bash
sudo nmcli connection up drone
```

On iPad or Mac, connect to Wi-Fi `drone` and open:

```text
http://10.42.0.1:8080
```

Return to normal Wi-Fi:

```bash
sudo nmcli connection down drone
sudo nmcli connection up CharlesZhang
```

## Hardware Check

- Battery charged and secured.
- Props installed only when ready for outdoor flight.
- Props undamaged and mounted in the correct direction.
- Frame, arms, camera mount, Pi mount, and Pixhawk mount are tight.
- RealSense is connected and firmly mounted.
- Pixhawk serial cable is connected to the Pi.
- RC is powered on and bound.
- QGroundControl can see the vehicle.
- Position/GPS/home checks are healthy before autonomous tests.
- Test area is open, flat, and far away from people.

## Software Check

On the Pi:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
```

Confirm Pixhawk serial exists:

```bash
ls -l /dev/serial0
```

Confirm the main files are present:

```bash
ls -1 11_follow_safe.py safety_supervisor_v2.py 12_takeoff_hover_land_test.py
```

## Test Order

### 1. Bench Test Without Props

Run the follow program in dry mode:

```bash
python -u 11_follow_safe.py
```

Open:

```text
http://10.0.0.105:8080
```

Expected:

- WebRTC video loads.
- Clicking a person locks the target.
- Terminal prints `[DRY]`.
- No Pixhawk movement commands are sent.

### 2. Outdoor Takeoff Hover Land

Use this before any follow test:

```bash
python -u 12_takeoff_hover_land_test.py --addr serial:///dev/serial0:57600 --alt 2.5 --hover 8 --real
```

Expected:

- Connects to Pixhawk.
- Waits for health checks.
- Arms only after typing `TAKEOFF`.
- Takes off to about 2.5 m.
- Holds for 8 seconds.
- Lands automatically.

Keep RC ready to switch to Position or Stabilized at any moment.

### 3. Outdoor Follow Dry Run

Run:

```bash
python -u 11_follow_safe.py
```

Expected:

- Target can be selected by click.
- `Locked YES` appears.
- `forward_cmd` and `yaw_cmd` look reasonable.
- Terminal remains in `[DRY]` mode.

### 4. Real Follow Short Test

Only after the earlier tests pass:

```bash
FOLLOW_REAL=1 python -u 11_follow_safe.py
```

Start with very short, low-speed motion. Keep the RC ready and switch out of Offboard immediately if behavior looks wrong.

## Abort Rules

Abort immediately if any of these happen:

- Wrong target is locked.
- Video freezes while real follow is active.
- Vehicle yaws or moves unexpectedly.
- Position/GPS becomes unhealthy.
- RC link or operator confidence is lost.
- Person walks near obstacles or other people.

Manual takeover:

```text
Switch RC mode to Position or Stabilized.
```

## GitHub Files To Keep

Keep these in the repository:

- `scripts/safety_supervisor_v2.py`
- `scripts/12_takeoff_hover_land_test.py`
- `11_follow_safe.py`
- `10_webrtc_follow_udp_test.py` if kept as an experiment/archive.
- `docs/field_ops/field_test_checklist.md`

Do not keep generated files or local backups:

- `__pycache__/`
- `.DS_Store`
- `*.backup*`
- `*.broken_backup*`
- `*.before_transfer*`
- `logs/`
