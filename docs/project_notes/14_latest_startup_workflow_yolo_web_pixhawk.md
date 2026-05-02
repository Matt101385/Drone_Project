# 14 Latest Startup Workflow: YOLO, Web, and Pixhawk

## Purpose

Record the latest practical startup workflow.

## Latest Vision Program

Historical command:

```bash
cd ~/follow_project
source .venv/bin/activate
python stream_mjpeg_yolo.py
```

After GitHub cleanup and renaming:

```bash
cd ~/matt_drone/follow_project
source .venv/bin/activate
python 07_latest_yolo_person_follow_click_target_stream.py
```

## Website Startup

```bash
cd ~/my-app
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Pixhawk Heartbeat Check

```bash
cd ~
source ~/px4env/bin/activate
mavproxy.py --master=/dev/serial0 --baudrate 57600
```

Success:

```text
Detected vehicle 1:1 on link 0
online system 1
Mode LOITER
```

## Recommended Order

1. Start YOLO stream.
2. Start website.
3. Check Pixhawk heartbeat when needed.
