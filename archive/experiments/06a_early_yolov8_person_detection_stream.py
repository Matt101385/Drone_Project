import time, threading
import numpy as np
import pyrealsense2 as rs
import cv2
from flask import Flask, Response
from ultralytics import YOLO

WIDTH, HEIGHT, FPS = 640, 480, 30
PORT = 8000

app = Flask(__name__)
latest_jpeg = None
lock = threading.Lock()

def camera_loop():
    global latest_jpeg

    # 第一次运行会自动下载模型（需要Pi能上网）
    model = YOLO("yolov8n.pt")

    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    pipeline.start(cfg)

    last_t = time.time()
    frames_for_fps = 0
    fps_est = 0.0

    detect_every_n = 2   # 每2帧跑一次YOLO
    last_box = None

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

            i += 1
            if (i % detect_every_n) == 0:
                # 只检测 person(类别0)
                r = model.predict(img, imgsz=640, conf=0.35, classes=[0], verbose=False)[0]
                best = None
                best_area = 0
                if r.boxes is not None and len(r.boxes) > 0:
                    for b in r.boxes:
                        x1, y1, x2, y2 = b.xyxy[0].cpu().numpy().astype(int)
                        area = (x2 - x1) * (y2 - y1)
                        if area > best_area:
                            best_area = area
                            best = (x1, y1, x2, y2, float(b.conf[0]))
                last_box = best
            else:
                best = last_box

            # overlay
            cv2.putText(img, f"FPS {fps_est:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
            cv2.drawMarker(img, (cx_img, cy_img), (0,255,0),
                           cv2.MARKER_CROSS, 20, 2)

            if best is not None:
                x1, y1, x2, y2, conf = best
                cx_p, cy_p = (x1 + x2)//2, (y1 + y2)//2
                dx, dy = cx_p - cx_img, cy_p - cy_img

                cv2.rectangle(img, (x1,y1), (x2,y2), (0,0,255), 3)
                cv2.circle(img, (cx_p, cy_p), 6, (0,0,255), -1)
                cv2.line(img, (cx_img, cy_img), (cx_p, cy_p), (255,0,0), 3)
                cv2.putText(img, f"person conf={conf:.2f} dx={dx} dy={dy}", (10, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            else:
                cv2.putText(img, "No person", (10, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

            ok, jpg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
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

@app.route("/stream")
def stream():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    threading.Thread(target=camera_loop, daemon=True).start()
    print(f"✅ YOLO person stream on http://0.0.0.0:{PORT}/stream")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
