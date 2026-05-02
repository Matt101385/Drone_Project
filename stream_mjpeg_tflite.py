import time
import threading
import numpy as np
import pyrealsense2 as rs
import cv2
from flask import Flask, Response
import os
import logging
from datetime import datetime
import tflite_runtime.interpreter as tflite

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
logger.info("TFLite stream program started")

# =========================
# Basic Config
# =========================
WIDTH, HEIGHT, FPS = 424, 240, 30
FRAME_TIMEOUT_MS = 1000
MAX_LOST = 5
RESTART_WAIT_SEC = 2
DETECT_EVERY_N_FRAMES = 5
CONF_THRESHOLD = 0.45

MODEL_PATH = os.path.expanduser("~/follow_project/models/detect.tflite")
LABEL_PATH = os.path.expanduser("~/follow_project/models/labelmap.txt")

app = Flask(__name__)

latest_jpeg = None
lock = threading.Lock()

pipeline = None
cfg = None
latest_detections = []

# =========================
# Labels
# =========================
def load_labels(path):
    labels = {}
    with open(path, "r") as f:
        for i, line in enumerate(f):
            labels[i] = line.strip()
    return labels

labels = load_labels(LABEL_PATH)

# =========================
# TFLite init
# =========================
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_index = input_details[0]["index"]
input_shape = input_details[0]["shape"]
input_height = input_shape[1]
input_width = input_shape[2]
input_dtype = input_details[0]["dtype"]

logger.info(f"TFLite model loaded: {MODEL_PATH}")

# =========================
# RealSense helpers
# =========================
def start_pipeline():
    global pipeline, cfg
    logger.info("Starting RealSense pipeline")
    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.rgb8, FPS)
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
# Detection
# =========================
def run_tflite_detection(frame_bgr):
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (input_width, input_height))
    input_data = np.expand_dims(resized, axis=0)

    if input_dtype == np.float32:
        input_data = input_data.astype(np.float32) / 255.0
    else:
        input_data = input_data.astype(input_dtype)

    interpreter.set_tensor(input_index, input_data)
    interpreter.invoke()

    boxes = interpreter.get_tensor(output_details[0]["index"])[0]
    classes = interpreter.get_tensor(output_details[1]["index"])[0]
    scores = interpreter.get_tensor(output_details[2]["index"])[0]
    count = int(interpreter.get_tensor(output_details[3]["index"])[0])

    results = []
    h, w = frame_bgr.shape[:2]

    for i in range(count):
        score = float(scores[i])
        if score < CONF_THRESHOLD:
            continue

        ymin, xmin, ymax, xmax = boxes[i]
        x1 = int(max(0, xmin * w))
        y1 = int(max(0, ymin * h))
        x2 = int(min(w, xmax * w))
        y2 = int(min(h, ymax * h))

        class_id = int(classes[i])
        label = labels.get(class_id, f"id_{class_id}")

        results.append({
            "bbox": (x1, y1, x2, y2),
            "score": score,
            "label": label,
        })

    return results

# =========================
# Camera Loop
# =========================
def camera_loop():
    global latest_jpeg, latest_detections

    lost_count = 0
    frame_count = 0
    fps_est = 0.0
    last_t = time.time()
    detect_counter = 0

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
            else:
                img = np.asanyarray(color_frame.get_data())
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                detect_counter += 1
                infer_ms = 0.0

                if detect_counter % DETECT_EVERY_N_FRAMES == 0:
                    t0 = time.time()
                    latest_detections = run_tflite_detection(img)
                    infer_ms = (time.time() - t0) * 1000.0

                det_count = len(latest_detections)

                for det in latest_detections:
                    x1, y1, x2, y2 = det["bbox"]
                    score = det["score"]
                    label = det["label"]

                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        img,
                        f"{label} {score:.2f}",
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

                h, w = img.shape[:2]
                cx, cy = w // 2, h // 2
                cv2.drawMarker(img, (cx, cy), (0, 255, 255), cv2.MARKER_CROSS, 20, 2)

                frame_count += 1
                now = time.time()
                if now - last_t >= 1.0:
                    fps_est = frame_count / (now - last_t)
                    frame_count = 0
                    last_t = now

                cv2.putText(img, f"FPS {fps_est:.1f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(img, f"Objects {det_count}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(img, f"Infer {infer_ms:.1f} ms", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                ok, jpg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ok:
                    continue

                with lock:
                    latest_jpeg = jpg.tobytes()

                lost_count = 0

        except Exception as e:
            lost_count += 1
            logger.warning(f"WARNING camera lost: {e}, lost_count={lost_count}")

        if lost_count >= MAX_LOST:
            recovered = restart_pipeline()
            if recovered:
                lost_count = 0
            else:
                with lock:
                    latest_jpeg = generate_placeholder_jpeg("Camera reconnecting...")
                time.sleep(1)

# =========================
# MJPEG Generator
# =========================
def mjpeg_generator():
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
      <head><title>RealSense TFLite Stream</title></head>
      <body>
        <h2>RealSense TFLite Stream</h2>
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

if __name__ == "__main__":
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()

    print("Streaming on http://0.0.0.0:8000/stream")
    app.run(host="0.0.0.0", port=8000, threaded=True)