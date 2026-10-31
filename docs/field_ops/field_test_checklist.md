# Field Test Checklist

This checklist is for the Raspberry Pi 5 + Hailo-10H + Pixhawk 6X + Intel RealSense D435i person-following drone. The owner reports PX4 EKF set to `Range Finder`; verify the actual setting and sensor health in QGroundControl. The Pi follow program does not read LiDAR directly and provides no obstacle avoidance. See the [LiDAR reference](../reference/lidar_reference.md).

## Operating Modes

Use home or phone Wi-Fi while developing:

```bash
ssh matt@10.0.0.105
```

Use the Pi hotspot only in the field:

```bash
sudo nmcli connection up drone
```

On an iPad or Mac, connect to Wi-Fi `drone` and open:

```text
http://10.42.0.1:8080
```

Return to normal Wi-Fi:

```bash
sudo nmcli connection down drone
sudo nmcli connection up CharlesZhang
```

## Project Location

The active Raspberry Pi project must use the same structure and filenames as GitHub:

```bash
cd ~/Drone_Project
source .venv/bin/activate
```

Main files:

```text
src/follow_drone.py
src/hailo_person_detector.py
docs/field_ops/field_test_checklist.md
```

Do not run numbered development filenames such as `11_follow_safe.py` or `13_takeoff_hover_land_test.py`.

## Hardware Check

* Flight battery is charged and secured.
* Props are installed only when ready for outdoor flight.
* Props are undamaged and mounted in the correct direction.
* Frame, arms, camera mount, Raspberry Pi mount, AI HAT, and Pixhawk mount are tight.
* Intel RealSense D435i is connected and firmly mounted.
* LiDAR (if installed) is securely mounted and powered; identify its model/interface. Verify PX4 reports valid rangefinder data if using EKF Range Finder. This does not provide obstacle avoidance.
* Hailo-10H AI HAT and its heatsink are firmly installed.
* Raspberry Pi active cooling is operating.
* Raspberry Pi, AI HAT, and RealSense use a suitable regulated power supply.
* The Raspberry Pi is not powered through the Pixhawk TELEM2 port.
* Pixhawk serial cable is connected to the Raspberry Pi.
* RC transmitter is powered on and bound.
* Verify actual TELEM2 baud: the main-program default is 921600; the reference records 57600 from an earlier setup. Confirm the configured connection before proceeding.
* QGroundControl can see the vehicle.
* Position, GPS, home-position, and battery checks are healthy.
* Test area is open, flat, and far from people and obstacles.
* A safety observer is present during real flight.

## Software Check

Confirm the project is current:

```bash
cd ~/Drone_Project
git status --short  # preserve/resolve local changes before syncing
git pull --ff-only origin main
source .venv/bin/activate
```

Confirm the Pixhawk serial device exists:

```bash
ls -l /dev/serial0
```

Confirm the main files are present:

```bash
ls -1 \
  src/follow_drone.py \
  src/hailo_person_detector.py
```

Check Python syntax:

```bash
python -m py_compile \
  src/follow_drone.py \
  src/hailo_person_detector.py
```

Confirm the YOLO11n Hailo model exists:

```bash
find /usr/local/hailo/resources \
  -type f \
  -name 'yolov11n.hef'
```

Check Raspberry Pi power and temperature:

```bash
vcgencmd get_throttled
vcgencmd measure_temp
```

`get_throttled` should report:

```text
throttled=0x0
```

Do not proceed to real flight if undervoltage or thermal throttling is reported.

## Test Order

### 1. Bench Test Without Props

Remove all propellers.

Run the complete application in dry mode:

```bash
cd ~/Drone_Project
source .venv/bin/activate
FOLLOW_REAL=0 python -u src/follow_drone.py
```

Open:

```text
http://<raspberry-pi-ip>:8080
```

Expected:

* Terminal prints the Hailo HEF path.
* WebRTC video loads.
* A red box appears around a detected person.
* Clicking a person locks the target.
* The video shows `LOCKED` and the status panel shows `Locked: True`.
* Terminal prints `[DRY]`.
* No real Pixhawk movement commands are sent.
* No repeated `HAILO ERROR` messages appear.
* Video remains responsive.
* Hailo inference remains stable.

### 2. Command-Stability Dry Test

Keep the aircraft without propellers and remain in dry mode.

Test the following:

* Person stands still at approximately the target distance.
* Person moves slowly left and right.
* Person moves slowly toward and away from the camera.
* Person briefly leaves and re-enters the image.
* A second person enters the image.

Pass criteria:

* The selected person remains locked.
* The target does not unexpectedly switch to another person.
* Forward/yaw visual guidance changes smoothly. The controller uses distance and image-position errors to generate bounded position/yaw targets; the displayed forward guidance is not a flight-speed limit.
* Commands return toward zero when the target is centered and near the target distance.
* Loss of valid depth does not produce unsafe commands.
* With no valid target, visual guidance is zero. The controller latches the latest available N/E position once, retains the entry D target and retains the previous yaw target.
* No rapid repeated switching occurs between maximum speed and zero.

### 3. Outdoor Takeoff, Hover, and Land Test

The previously referenced `tests/hardware/takeoff_hover_land_test.py` is not present on `main`. Do not use the old command as a current procedure. Establish and independently verify a suitable takeoff, hover, and landing procedure before attempting this stage. The previous script is available in Git history for inspection, but its presence there does not establish that it is suitable for the current vehicle.

### 4. Outdoor Follow Dry Run

Place the aircraft in the planned test area but keep real follow disabled:

```bash
cd ~/Drone_Project
source .venv/bin/activate
FOLLOW_REAL=0 python -u src/follow_drone.py
```

Expected:

* Target can be selected by clicking.
* `Locked: True` remains stable when the intended person is selected.
* Person detection remains reliable in outdoor lighting.
* Depth measurements remain available.
* Forward/yaw visual guidance and position-follow status look reasonable.
* Terminal remains in `[DRY]` mode.
* Wi-Fi and WebRTC remain stable at the intended operating distance.

### 5. Real Follow Short Test

Only proceed after all earlier tests pass and the unresolved control issues in the README have been reviewed and validated. `FOLLOW_REAL=1` automatically requests Offboard after connection and initial pose acquisition; it does not wait for a separate confirmation.

Use a large, open test area. Start with short, slow movement:

```bash
cd ~/Drone_Project
source .venv/bin/activate
FOLLOW_REAL=1 python -u src/follow_drone.py
```

Requirements:

* RC operator is ready for immediate manual takeover.
* Safety observer is present.
* Target begins near the desired following distance.
* Target moves slowly and predictably.
* Test duration remains short.
* No obstacles or other people are near the flight path.
* Flight logs are reviewed before increasing speed or test duration.

## Abort Rules

Abort immediately if any of the following occurs:

* Wrong person is locked.
* Target unexpectedly switches between people.
* Person box disappears repeatedly.
* Video freezes or becomes severely delayed.
* Repeated `HAILO ERROR` messages appear.
* Depth becomes unavailable or unstable.
* Guidance or position/yaw setpoints oscillate rapidly.
* Vehicle yaws, climbs, descends, or moves unexpectedly.
* Position or GPS becomes unhealthy.
* Raspberry Pi reports undervoltage or thermal throttling.
* RC link, Wi-Fi link, or operator confidence is lost.
* Person approaches an obstacle or another person.

Manual takeover:

```text
Switch the RC flight mode to Position or Stabilized immediately.
```

## GitHub Files To Keep

Keep these current files in the repository:

```text
src/follow_drone.py
src/hailo_person_detector.py
docs/field_ops/field_test_checklist.md
README.md
docs/reference/lidar_reference.md
```

Do not commit generated or machine-specific files:

```text
.venv/
__pycache__/
*.pyc
.DS_Store
logs/
flight_*.csv
stream_*.log
test_person.jpg
*_backup.py
*.hef
```
