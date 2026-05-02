import time
import threading
import numpy as np
import pyrealsense2 as rs
import cv2
from flask import Flask, Response
import os
import logging
from datetime import datetime

# =========================
# Logging
# =========================
log_dir = os.path.expanduser("~/follow_project/logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(
    log_dir,
    f"stream_{datetime.now().strftime('%Y%m%d')}.log"
)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger()
logger.info("Stream program started")

# =========================
# Basic Config
# =========================
WIDTH, HEIGHT, FPS = 640, 480, 30
FRAME_TIMEOUT_MS = 1000
MAX_LOST = 5
RESTART_WAIT_SEC = 2

app = Flask(__name__)

latest_jpeg = None
lock = threading.Lock()

pipeline = None
cfg = None


# =========================
# RealSense helpers
# =========================
def start_pipeline():
    global pipeline, cfg

    logger.info("Starting RealSense pipeline")
    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    pipeline.start(cfg)
    logger.info("RealSense pipeline started successfully")


def stop_pipeline():
    global pipeline
    if pipeline is not None:
        try:
            pipeline.stop()
            logger.info("RealSense pipeline stopped")
        except Exception as e:
            logger.warning(f"Pipeline stop warning: {e}")
        finally:
            pipeline = None


def restart_pipeline():
    logger.warning("Restarting RealSense pipeline")
    stop_pipeline()
    time.sleep(RESTART_WAIT_SEC)
    try:
        start_pipeline()
        logger.info("Pipeline restarted successfully")
        return True
    except Exception as e:
        logger.error(f"Pipeline restart failed: {e}")
        return False


def generate_placeholder_jpeg(text="Camera reconnecting..."):
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    cv2.putText(
        img,
        text,
        (30, HEIGHT // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2
    )
    ok, jpg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if ok:
        return jpg.tobytes()
    return None


# =========================
# Camera Loop
# =========================
def camera_loop():
    global latest_jpeg

    lost_count = 0
    frame_count = 0
    fps_est = 0.0
    last_t = time.time()

    try:
        start_pipeline()
    except Exception as e:
        logger.error(f"Initial pipeline start failed: {e}")
        with lock:
            latest_jpeg = generate_placeholder_jpeg("Camera start failed")
        return

    while True:
        try:
            if pipeline is None:
                logger.warning("Pipeline is None, attempting restart")
                recovered = restart_pipeline()
                if not recovered:
                    with lock:
                        latest_jpeg = generate_placeholder_jpeg("Camera reconnect failed")
                    time.sleep(1)
                    continue

            frames = pipeline.wait_for_frames(timeout_ms=FRAME_TIMEOUT_MS)
            color_frame = frames.get_color_frame()

            if not color_frame:
                lost_count += 1
                logger.warning(f"WARNING camera lost: empty color frame, lost_count={lost_count}")
            else:
                img = np.asanyarray(color_frame.get_data())

                # ===== Overlay =====
                h, w = img.shape[:2]
                cx, cy = w // 2, h // 2
                cv2.drawMarker(img, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

                frame_count += 1
                now = time.time()
                if now - last_t >= 1.0:
                    fps_est = frame_count / (now - last_t)
                    frame_count = 0
                    last_t = now
                    logger.info(f"FPS {fps_est:.1f}")

                cv2.putText(
                    img,
                    f"FPS {fps_est:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2
                )

                ok, jpg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ok:
                    logger.warning("JPEG encode failed")
                    continue

                with lock:
                    latest_jpeg = jpg.tobytes()

                lost_count = 0

        except Exception as e:
            lost_count += 1
            logger.warning(f"WARNING camera lost: {e}, lost_count={lost_count}")

        if lost_count >= MAX_LOST:
            logger.warning("Camera considered lost, attempting recovery")
            recovered = restart_pipeline()
            if recovered:
                lost_count = 0
                with lock:
                    if latest_jpeg is None:
                        latest_jpeg = generate_placeholder_jpeg("Camera recovered")
            else:
                with lock:
                    latest_jpeg = generate_placeholder_jpeg("Camera reconnecting...")
                time.sleep(1)


# =========================
# MJPEG Generator
# =========================
def mjpeg_generator():
    logger.info("MJPEG stream client connected")
    while True:
        with lock:
            frame = latest_jpeg

        if frame is None:
            frame = generate_placeholder_jpeg("Waiting for camera...")
            time.sleep(0.1)

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )

        time.sleep(0.001)


# =========================
# Flask Routes
# =========================
@app.route("/")
def index():
    return """
    <html>
      <head><title>RealSense MJPEG Stream</title></head>
      <body>
        <h2>RealSense MJPEG Stream</h2>
        <p>Open <a href="/stream">/stream</a></p>
        <img src="/stream" width="640">
      </body>
    </html>
    """


@app.route("/stream")
def stream():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# Main
# =========================
if __name__ == "__main__":
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()

    logger.info("Streaming on http://0.0.0.0:8000/stream")
    print("✅ Streaming on http://0.0.0.0:8000/stream")
    app.run(host="0.0.0.0", port=8000, threaded=True)
