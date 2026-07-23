# 05 Web Hosting, RealSense, and AI Architecture

## Purpose

Record the Raspberry Pi web-hosting experiment and the early RealSense + AI streaming architecture.

## Next.js Dashboard

Project:

```bash
npx create-next-app@latest my-app
cd ~/my-app
npm run dev
```

URLs:

```text
http://localhost:3000
http://10.0.0.168:3000
```

Dashboard information:

- Hostname.
- Platform.
- CPU temperature.
- CPU usage.
- Memory usage.

## Cloudflare Tunnel

Install:

```bash
sudo apt update
sudo apt install cloudflared
```

Quick tunnel:

```bash
cloudflared tunnel --url http://localhost:3000
```

## Early RealSense + AI Architecture

Target pipeline:

```text
RealSense -> AI object detection -> MJPEG stream -> Next.js -> Cloudflare Tunnel
```

## Two-Service TFLite Architecture

Because RealSense and TFLite used different Python environments:

```text
vision_env: stream_mjpeg.py on port 8000
tflite310_env: tflite_detect_proxy.py on port 8001
```

Startup:

```bash
source ~/vision_env/bin/activate
python ~/follow_project/stream_mjpeg.py
```

```bash
source ~/tflite310_env/bin/activate
python ~/follow_project/tflite_detect_proxy.py
```

## Important Fixes

NumPy conflict:

```bash
pip install numpy==1.26.4
```

If the AI proxy cannot connect, start the raw stream on port 8000 first.

## Key Takeaway

This was the first working web + camera + AI architecture, later simplified by the YOLO single-environment approach.
