# Current Startup Workflow

## Main Program

Current safe follow entry point:

```text
scripts/11_follow_safe.py
```

It runs:

- RealSense color/depth capture.
- YOLO person detection.
- WebRTC browser stream on port `8080`.
- Click-to-select target.
- Dry command preview by default.
- Optional real Pixhawk control with `FOLLOW_REAL=1`.
- Safety supervision through `scripts/safety_supervisor_v2.py`.

## Start Pi Environment

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
```

Check:

```bash
which python
python --version
```

## Dry Follow Mode

Use this first. It runs vision and command preview without sending movement commands to Pixhawk.

```bash
python -u scripts/11_follow_safe.py
```

Open from normal Wi-Fi:

```text
http://10.0.0.105:8080
```

Open from Pi hotspot:

```text
http://10.42.0.1:8080
```

Expected terminal output includes:

```text
[DRY] FOLLOW_REAL is not 1; vision runs, Pixhawk commands are not sent.
```

## Takeoff Hover Land Smoke Test

Run before real follow testing:

```bash
python -u scripts/13_takeoff_hover_land_test.py --addr serial:///dev/serial0:57600 --alt 2.5 --hover 8 --real
```

The script arms only after typing:

```text
TAKEOFF
```

## Real Follow Mode

Only use after bench test, smoke test, outdoor dry run, and RC takeover checks pass.

```bash
FOLLOW_REAL=1 python -u scripts/11_follow_safe.py
```

Keep RC ready to switch out of Offboard immediately.

## Pixhawk Heartbeat Check

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Expected output includes:

```text
Detected vehicle 1:1 on link 0
online system 1
```

## Recommended Test Order

1. Bench dry mode without props.
2. Outdoor takeoff/hover/land smoke test.
3. Outdoor follow dry run.
4. Short real follow test.

## Abort Rules

Abort immediately if:

- Wrong target is locked.
- Video freezes during real follow.
- Vehicle moves unexpectedly.
- Position/GPS/home becomes unhealthy.
- RC link or pilot confidence is lost.
- Person walks near obstacles or other people.
