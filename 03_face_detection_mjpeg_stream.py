import time
import threading
import numpy as np
import pyrealsense2 as rs
import cv2
from flask import Flask, Response

WIDTH, HEIGHT, FPS = 640, 480, 30
PORT = 8000

app = Flask(__name__)
latest_jpeg = None
lock = threading.Lock()

def get_cascade():
    # OpenCV pip 包通常自带 haarcascade 文件目录
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        raise RuntimeError(f"Failed to load cascade at: {cascade_path}")
    return cascade

def camera_loop():
    global latest_jpeg

    face_cascade = get_cascade()

    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    pipeline.start(cfg)

    last_t = time.time()
    frame_count = 0
    fps_est = 0.0

    # 为了省 CPU：每 N 帧做一次检测，其余帧沿用上次结果
    detect_every_n = 2
    last_faces = []

    try:
        while True:
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            c = frames.get_color_frame()
            if not c:
                continue

            img = np.asanyarray(c.get_data())
            h, w = img.shape[:2]
            cx_img, cy_img = w // 2, h // 2

            # FPS 统计
            frame_count += 1
            now = time.time()
            if now - last_t >= 1.0:
                fps_est = frame_count / (now - last_t)
                frame_count = 0
                last_t = now

            # ---- 人脸检测（轻量）----
            if (frame_count % detect_every_n) == 0:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)

                # 关键参数：scaleFactor/minNeighbors 会影响稳定性和误检
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(60, 60)
                )
                last_faces = faces
            else:
                faces = last_faces

            # ---- overlay 画图 ----
            cv2.putText(img, f"FPS {fps_est:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
            cv2.drawMarker(img, (cx_img, cy_img), (0,255,0),
                           markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)

            if len(faces) > 0:
                # 选最大的人脸（最接近镜头）
                x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])
                x2, y2 = x + fw, y + fh
                cx_f, cy_f = x + fw // 2, y + fh // 2
                dx, dy = cx_f - cx_img, cy_f - cy_img

                cv2.rectangle(img, (x, y), (x2, y2), (0,0,255), 3)
                cv2.circle(img, (cx_f, cy_f), 6, (0,0,255), -1)
                cv2.line(img, (cx_img, cy_img), (cx_f, cy_f), (255,0,0), 3)
                cv2.putText(img, f"dx={dx} dy={dy}", (10, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            else:
                cv2.putText(img, "No face", (10, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

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
    return "<h2>RealSense Face Stream</h2><p>Open <a href='/stream'>/stream</a></p>"

@app.route("/stream")
def stream():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()
    print(f"✅ Face stream on http://0.0.0.0:{PORT}/stream")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
