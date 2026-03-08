import time
import threading
import numpy as np
import pyrealsense2 as rs
import cv2
from flask import Flask, Response

# 为了速度：先用较低分辨率
WIDTH, HEIGHT, FPS = 640, 480, 30
PORT = 8000

app = Flask(__name__)
latest_jpeg = None
lock = threading.Lock()

def camera_loop():
    global latest_jpeg

    # HOG 行人检测器（OpenCV 自带）
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    pipeline.start(cfg)

    last_t = time.time()
    frames_for_fps = 0
    fps_est = 0.0

    detect_every_n = 6   # 每3帧检测一次，省CPU
    last_boxes = []

    try:
        i = 0
        while True:
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            c = frames.get_color_frame()
            if not c:
                continue

            img = np.asanyarray(c.get_data())
            h, w = img.shape[:2]
            cx_img, cy_img = w // 2, h // 2

            # FPS
            frames_for_fps += 1
            now = time.time()
            if now - last_t >= 1.0:
                fps_est = frames_for_fps / (now - last_t)
                frames_for_fps = 0
                last_t = now

            # 行人检测
            i += 1
            if (i % detect_every_n) == 0:
                # HOG 对更大输入更准，但更慢；这里保持原尺寸
                boxes, weights = hog.detectMultiScale(
                    img,
                    winStride=(4, 4),
                    padding=(8, 8),
                    scale=1.05
                )

                # 过滤弱结果（阈值可调）
                filtered = []
                for (x, y, bw, bh), wt in zip(boxes, weights):
                    if wt < 0.3:
                        continue
                    filtered.append((int(x), int(y), int(bw), int(bh), float(wt)))
                last_boxes = filtered
            else:
                filtered = last_boxes

            # overlay
            cv2.putText(img, f"FPS {fps_est:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.drawMarker(img, (cx_img, cy_img), (0,255,0),
                           markerType=cv2.MARKER_CROSS, markerSize=16, thickness=2)

            if len(filtered) > 0:
                # 取最大框（默认最近的人）
                x, y, bw, bh, wt = max(filtered, key=lambda r: r[2] * r[3])
                x2, y2 = x + bw, y + bh
                cx_p, cy_p = x + bw // 2, y + bh // 2
                dx, dy = cx_p - cx_img, cy_p - cy_img

                cv2.rectangle(img, (x, y), (x2, y2), (0,0,255), 2)
                cv2.circle(img, (cx_p, cy_p), 5, (0,0,255), -1)
                cv2.line(img, (cx_img, cy_img), (cx_p, cy_p), (255,0,0), 2)
                cv2.putText(img, f"person wt={wt:.2f} dx={dx} dy={dy}", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2)
            else:
                cv2.putText(img, "No person", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

            ok, jpg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue

            with lock:
                latest_jpeg = jpg.tobytes()

    finally:
        pipeline.stop()

def mjpeg_generator():
    while True:
        with lock:
            frame = latest_jpeg
        if frame is None:
            time.sleep(0.01)
            continue
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.001)

@app.route("/")
def index():
    return "<h2>RealSense Person(HOG) Stream</h2><p>Open <a href='/stream'>/stream</a></p>"

@app.route("/stream")
def stream():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()
    print(f"✅ Person(HOG) stream on http://0.0.0.0:{PORT}/stream")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
