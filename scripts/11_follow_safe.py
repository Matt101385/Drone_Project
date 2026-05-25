import time
import threading
import numpy as np
import pyrealsense2 as rs
import cv2
from flask import Flask, Response, request, jsonify
import os
import logging
from datetime import datetime
from ultralytics import YOLO
# 新增
import asyncio

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from safety_supervisor_v2 import SafetyLimits, SafetySupervisorV2



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
logger.info("YOLO stream program started")

# =========================
# Basic Config
# =========================
WIDTH, HEIGHT, FPS = 640, 480, 15
FRAME_TIMEOUT_MS = 1000
MAX_LOST = 5
RESTART_WAIT_SEC = 2

MODEL_PATH = "yolo11n.pt"
CONF_THRES = 0.4

# yaw control preview only
Kp = 8.0
DEADBAND = 0.08
MAX_YAW_CMD = 10.0
# forward distance control preview only
TARGET_DIST_M = 4.0
DIST_DEADBAND = 0.40
Kp_forward = 0.15
MAX_FORWARD_CMD = 0.15

DEPTH_MIN_M = 0.3
DEPTH_MAX_M = 6.0

app = Flask(__name__)

latest_jpeg = None
latest_frame = None
webrtc_pcs = set()
lock = threading.Lock()
current_person_boxes = []
selected_click = None
selected_target = None
pipeline = None
cfg = None
align = None
target_lost_count = 0
MAX_TARGET_LOST = 8

FOLLOW_REAL = os.environ.get("FOLLOW_REAL") == "1"
PX4_ADDR = os.environ.get("PX4_ADDR", "serial:///dev/serial0:57600")
FOLLOW_COMMAND_HZ = 10
FOLLOW_COMMAND_INTERVAL = 1.0 / FOLLOW_COMMAND_HZ

latest_follow_command = {
    "forward_m_s": 0.0,
    "right_m_s": 0.0,
    "down_m_s": 0.0,
    "yaw_deg_s": 0.0,
    "target_locked": False,
    "source": "no-target",
    "updated_monotonic": time.monotonic(),
}
# =========================
# YOLO model
# =========================
try:
    model = YOLO(MODEL_PATH)
    logger.info(f"YOLO model loaded: {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    model = None

# =========================
# RealSense helpers
# =========================
def start_pipeline():
    global pipeline, cfg, align

    logger.info("Starting RealSense pipeline")
    pipeline = rs.pipeline()
    cfg = rs.config()
    
    cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    cfg.enable_stream(rs.stream.depth, WIDTH, HEIGHT, rs.format.z16, FPS)
    
    pipeline.start(cfg)
    
    align = rs.align(rs.stream.color)
    logger.info(f"align created: {align is not None}")
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
        (40, HEIGHT // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
    if not ok:
        return None
    return buf.tobytes()


def point_in_box(px, py, box):
    return box["x1"] <= px <= box["x2"] and box["y1"] <= py <= box["y2"]


def get_target_distance(depth_frame, cx, cy, box, win=5):
    x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]

    samples = []
    for dy in range(-win, win + 1):
        for dx in range(-win, win + 1):
            px = int(cx + dx)
            py = int(cy + dy)

            if px < x1 or px > x2 or py < y1 or py > y2:
                continue
            if px < 0 or py < 0 or px >= WIDTH or py >= HEIGHT:
                continue

            d = depth_frame.get_distance(px, py)
            if DEPTH_MIN_M <= d <= DEPTH_MAX_M:
                samples.append(d)

    if not samples:
        return None

    return float(np.median(samples))

def update_follow_command(
    forward_m_s,
    right_m_s,
    down_m_s,
    yaw_deg_s,
    target_locked,
    source,
):
    with lock:
        latest_follow_command["forward_m_s"] = float(forward_m_s)
        latest_follow_command["right_m_s"] = float(right_m_s)
        latest_follow_command["down_m_s"] = float(down_m_s)
        latest_follow_command["yaw_deg_s"] = float(yaw_deg_s)
        latest_follow_command["target_locked"] = bool(target_locked)
        latest_follow_command["source"] = str(source)
        latest_follow_command["updated_monotonic"] = time.monotonic()


def read_follow_command():
    with lock:
        return dict(latest_follow_command)



async def wait_until_connected(drone):
    print(f"[PX4] connecting to {PX4_ADDR} ...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[PX4] connected")
            return


async def follow_control_loop():
    if not FOLLOW_REAL:
        print("[DRY] FOLLOW_REAL is not 1; vision runs, Pixhawk commands are not sent.")
        last_print = 0.0
        while True:
            cmd = read_follow_command()
            now = time.monotonic()
            if now - last_print >= 1.0:
                print(
                    "[DRY] "
                    f"locked={cmd['target_locked']} "
                    f"forward={cmd['forward_m_s']:+.2f} "
                    f"right={cmd['right_m_s']:+.2f} "
                    f"down={cmd['down_m_s']:+.2f} "
                    f"yaw={cmd['yaw_deg_s']:+.1f} "
                    f"source={cmd['source']} "
                    f"age={now - cmd['updated_monotonic']:.2f}s"
                )
                last_print = now
            await asyncio.sleep(0.1)

    from mavsdk import System
    from mavsdk.offboard import OffboardError, VelocityBodyYawspeed

    drone = System()
    await drone.connect(system_address=PX4_ADDR)
    await wait_until_connected(drone)

    supervisor = SafetySupervisorV2(
        drone,
        SafetyLimits(
            roll_limit_deg=25.0,
            pitch_limit_deg=25.0,
            command_timeout_s=0.7,
            max_forward_m_s=MAX_FORWARD_CMD,
            max_right_m_s=0.0,
            max_down_m_s=0.0,
            max_yaw_deg_s=MAX_YAW_CMD,
            max_forward_accel_m_s2=0.4,
            max_right_accel_m_s2=0.4,
            max_down_accel_m_s2=0.3,
            max_yaw_accel_deg_s2=30.0,
        ),
        limit_breach_action="warn",
        attitude_breach_action="warn",
        failsafe_action="hold",
    )
    await supervisor.install()

    try:
        print("[PX4] starting Offboard with zero velocity...")
        await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(0.2)

        try:
            await drone.offboard.start()
        except OffboardError as exc:
            print(f"[PX4] Offboard start failed: {exc}")
            return

        supervisor.mark_offboard_started()
        print("[PX4] Offboard active. Safety Supervisor is controlling commands.")

        while True:
            cmd = read_follow_command()
            now = time.monotonic()
            age = now - cmd["updated_monotonic"]

            if age > 0.5 or not cmd["target_locked"]:
                await supervisor.send_velocity_body(
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    source=f"hold-no-target-age-{age:.2f}s",
                )
            else:
                await supervisor.send_velocity_body(
                    cmd["forward_m_s"],
                    cmd["right_m_s"],
                    cmd["down_m_s"],
                    cmd["yaw_deg_s"],
                    source=cmd["source"],
                )

            await asyncio.sleep(1.0 / FOLLOW_COMMAND_HZ)

    finally:
        print("[PX4] cleanup: zero command, stop Offboard")
        try:
            await supervisor.send_zero("program exit")
        except Exception:
            pass
        try:
            await drone.offboard.stop()
        except Exception:
            pass
        await supervisor.uninstall()


def run_follow_control_loop():
    asyncio.run(follow_control_loop())


# =========================
# Camera Loop
# =========================
def camera_loop():
    global latest_jpeg, latest_frame, current_person_boxes, selected_click, selected_target, target_lost_count

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
                lost_count = 0

            try:
                frames = pipeline.wait_for_frames(timeout_ms=FRAME_TIMEOUT_MS)
                
                if align is None:
                    raise RuntimeError("align is None")
                aligned_frames = align.process(frames)
                
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
                
                if not color_frame or not depth_frame:
                    raise RuntimeError("No color frame")
                lost_count = 0
            except Exception as e:
                lost_count += 1
                logger.warning(f"CAMERA frame error: {e}, lost_count={lost_count}")

                if lost_count >= MAX_LOST:
                    logger.warning("Camera considered lost, attempting recovery")
                    recovered = restart_pipeline()
                    if recovered:
                        lost_count = 0
                        with lock:
                            latest_jpeg = generate_placeholder_jpeg("Camera recovered")
                    else:
                        with lock:
                            latest_jpeg = generate_placeholder_jpeg("Camera reconnect failed")
                        time.sleep(1)
                    continue

                time.sleep(0.05)
                continue

            color_image = np.asanyarray(color_frame.get_data())

            # ===== YOLO detection =====
            detect_start = time.time()
            det_count = 0
            person_boxes = []
            locked_target = None

            if model is not None:
                try:
                    results = model(color_image, imgsz=320, conf=CONF_THRES, verbose=False)

                    for result in results:
                        boxes = result.boxes
                        names = result.names
                        det_count += len(boxes)

                        for box in boxes:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                            class_name = names[cls_id]
                            label = f"{class_name} {conf:.2f}"

                            if class_name == "person" and conf >= CONF_THRES:
                                area = (x2 - x1) * (y2 - y1)
                                person_boxes.append({
                                    "x1": x1,
                                    "y1": y1,
                                    "x2": x2,
                                    "y2": y2,
                                    "cx": (x1 + x2) / 2.0,
                                    "cy": (y1 + y2) / 2.0,
                                    "area": area,
                                    "label": label,
                                })
                                color = (0, 0, 255)
                            else:
                                color = (0, 255, 0)

                            cv2.rectangle(color_image, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(
                                color_image,
                                label,
                                (x1, max(y1 - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                color,
                                2,
                            )

                except Exception as e:
                    logger.warning(f"YOLO inference failed: {e}")

            with lock:
                current_person_boxes = [dict(b) for b in person_boxes]

            with lock:
                click = dict(selected_click) if selected_click is not None else None

            # ===== click-select target =====
            if click is not None and len(person_boxes) > 0:
                hit_boxes = [
                    b for b in person_boxes
                    if point_in_box(click["x"], click["y"], b)
                ]
                if len(hit_boxes) > 0:
                    locked_target = min(hit_boxes, key=lambda b: b["area"])
                    with lock:
                        selected_target = dict(locked_target)
                        selected_click = None
                        
            # keep selected target across frames
            if locked_target is None:
                with lock:
                    prev_target = dict(selected_target) if selected_target is not None else None

                if prev_target is not None and len(person_boxes) > 0:
                    candidate = min(
                        person_boxes,
                        key=lambda b: (b["cx"] - prev_target["cx"]) ** 2 + (b["cy"] - prev_target["cy"]) ** 2
                    )

                    dx = candidate["cx"] - prev_target["cx"]
                    dy = candidate["cy"] - prev_target["cy"]
                    dist2 = dx * dx + dy * dy

                    # accept only if still close enough to previous target
                    if dist2 < 150 * 150:
                        locked_target = candidate
                        with lock:

                            selected_target = dict(locked_target)
                        target_lost_count = 0
                    else:
                        target_lost_count += 1

                elif prev_target is not None:
                    target_lost_count += 1

                if target_lost_count >= MAX_TARGET_LOST:
                    with lock:
                        selected_target = None
                    target_lost_count = 0

            #这是自动锁定最大的人的代码，暂时注释掉，避免误锁定
            # fallback: auto lock largest person
            #if locked_target is None and len(person_boxes) > 0:
            #   locked_target = max(person_boxes, key=lambda b: b["area"])

            # ===== yaw preview only =====
            h, w = color_image.shape[:2]
            img_cx = w / 2.0
            img_cy = h / 2.0

            error_x = 0.0
            err_norm = 0.0
            yaw_cmd = 0.0
            
            target_dist = None
            dist_error = 0.0
            forward_cmd = 0.0
            
            target_cx = None
            target_cy = None

            if locked_target is not None:
                x1 = locked_target["x1"]
                y1 = locked_target["y1"]
                x2 = locked_target["x2"]
                y2 = locked_target["y2"]
                target_cx = locked_target["cx"]
                target_cy = locked_target["cy"]

                cv2.rectangle(color_image, (x1, y1), (x2, y2), (255, 0, 0), 3)
                cv2.putText(
                    color_image,
                    "LOCKED",
                    (x1, max(y1 - 35, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 0, 0),
                    2,
                )
                cv2.circle(color_image, (int(target_cx), int(target_cy)), 5, (255, 0, 0), -1)

                error_x = target_cx - img_cx
                err_norm = error_x / img_cx

                if abs(err_norm) < DEADBAND:
                    yaw_cmd = 0.0
                else:
                    yaw_cmd = Kp * err_norm
                    yaw_cmd = max(min(yaw_cmd, MAX_YAW_CMD), -MAX_YAW_CMD)
                
                target_dist = get_target_distance(
                    depth_frame,
                    target_cx,
                    target_cy,
                    locked_target,
                    win=5
                )

                if target_dist is not None:
                    dist_error = target_dist - TARGET_DIST_M

                    if abs(dist_error) < DIST_DEADBAND:
                        forward_cmd = 0.0
                    else:
                        forward_cmd = Kp_forward * dist_error
                        forward_cmd = max(min(forward_cmd, MAX_FORWARD_CMD), -MAX_FORWARD_CMD)

                target_locked = locked_target is not None
                update_follow_command(
                    forward_m_s=float(forward_cmd if target_locked else 0.0),
                    right_m_s=0.0,
                    down_m_s=0.0,
                    yaw_deg_s=float(yaw_cmd if target_locked else 0.0),
                    target_locked=target_locked,
                    source="pi-vision-11",
                )

                cv2.line(
                    color_image,
                    (int(img_cx), int(img_cy)),
                    (int(target_cx), int(target_cy)),
                    (255, 255, 0),
                    2,
                )

            if locked_target is None:
                update_follow_command(
                    forward_m_s=0.0,
                    right_m_s=0.0,
                    down_m_s=0.0,
                    yaw_deg_s=0.0,
                    target_locked=False,
                    source="no-target",
                )
            infer_ms = (time.time() - detect_start) * 1000.0

            # ===== Overlay =====
            cv2.drawMarker(
                color_image,
                (int(img_cx), int(img_cy)),
                (0, 255, 255),
                cv2.MARKER_CROSS,
                20,
                2,
            )

            frame_count += 1
            now = time.time()
            if now - last_t >= 1.0:
                fps_est = frame_count / (now - last_t)
                frame_count = 0
                last_t = now
                logger.info(
                    f"FPS {fps_est:.1f}, detections {det_count}, persons {len(person_boxes)}, "
                    f"locked {locked_target is not None}, yaw_cmd {yaw_cmd:.3f}, infer {infer_ms:.1f} ms"
                )

            cv2.putText(color_image, f"FPS {fps_est:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"Detections {det_count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"Infer {infer_ms:.1f} ms", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"Persons {len(person_boxes)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"Locked {'YES' if locked_target is not None else 'NO'}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"error_x {error_x:.1f}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"err_norm {err_norm:.3f}", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(color_image, f"yaw_cmd {yaw_cmd:.3f}", (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            cv2.putText(
                color_image,
                f"dist {target_dist:.2f}m" if target_dist is not None else "dist N/A",
                (10, 270),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )

            cv2.putText(
                color_image,
                f"dist_err {dist_error:.2f}",
                (10, 300),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )

            cv2.putText(
                color_image,
                f"forward_cmd {forward_cmd:.3f}",
                (10, 330),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )
            
            with lock:
                latest_frame = color_image.copy()

            ok, jpg = cv2.imencode(".jpg", color_image, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ok:
                logger.warning("JPEG encode failed")
                continue

            with lock:
                latest_jpeg = jpg.tobytes()

        except Exception as e:
            logger.error(f"Main loop unexpected error: {e}")
            time.sleep(0.1)
            continue



class LatestFrameVideoTrack(VideoStreamTrack):
    async def recv(self):
        pts, time_base = await self.next_timestamp()

        while True:
            with lock:
                frame = None if latest_frame is None else latest_frame.copy()

            if frame is not None:
                break

            await asyncio.sleep(0.01)

        video_frame = VideoFrame.from_ndarray(np.ascontiguousarray(frame), format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame


WEBRTC_HTML = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <title>11 Follow Safe WebRTC</title>
</head>
<body style="margin:0;background:#111;color:white;font-family:sans-serif;">
    <main style="width:min(1100px,94vw);margin:24px auto;display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:18px;align-items:start;">
        <section>
            <video id="video" autoplay playsinline muted style="width:100%;background:#000;cursor:crosshair;"></video>
            <div id="status" style="margin-top:10px;color:#b7c0c7;">Connecting...</div>
        </section>

        <aside style="background:#1d1d1d;border:1px solid #444;border-radius:8px;padding:14px;font-size:18px;line-height:1.55;">
            <div>Mode: <span id="mode">DRY</span></div>
            <div>Locked: <span id="locked" style="color:#ff5555;">False</span></div>
            <div>Forward: <span id="forward" style="color:#ffd84d;">+0.00</span> m/s</div>
            <div>Right: <span id="right" style="color:#ffd84d;">+0.00</span> m/s</div>
            <div>Down: <span id="down" style="color:#ffd84d;">+0.00</span> m/s</div>
            <div>Yaw: <span id="yaw" style="color:#ffd84d;">+0.0</span> deg/s</div>
            <div>Source: <span id="source">no-target</span></div>
            <div>Age: <span id="age">0.00</span>s</div>
        </aside>
    </main>

    <script>
    function signed(value, digits) {
        const n = Number(value);
        return (n >= 0 ? "+" : "") + n.toFixed(digits);
    }

    async function refreshStatus() {
        try {
            const s = await fetch("/status").then(r => r.json());
            document.getElementById("mode").textContent = s.follow_real ? "REAL" : "DRY";

            const locked = document.getElementById("locked");
            locked.textContent = s.locked ? "True" : "False";
            locked.style.color = s.locked ? "#39ff88" : "#ff5555";

            document.getElementById("forward").textContent = signed(s.forward, 2);
            document.getElementById("right").textContent = signed(s.right, 2);
            document.getElementById("down").textContent = signed(s.down, 2);
            document.getElementById("yaw").textContent = signed(s.yaw, 1);
            document.getElementById("source").textContent = s.source;
            document.getElementById("age").textContent = Number(s.age).toFixed(2);
        } catch (e) {}
    }

    async function start() {
        const status = document.getElementById("status");
        const video = document.getElementById("video");

        const pc = new RTCPeerConnection();
        pc.addTransceiver("video", { direction: "recvonly" });

        pc.ontrack = (event) => {
            video.srcObject = event.streams[0];
            status.textContent = "WebRTC video connected";
        };

        pc.onconnectionstatechange = () => {
            status.textContent = "Connection: " + pc.connectionState;
        };

        video.addEventListener("click", async (event) => {
            const rect = video.getBoundingClientRect();
            const x = Math.round((event.clientX - rect.left) * 640 / rect.width);
            const y = Math.round((event.clientY - rect.top) * 480 / rect.height);

            await fetch("/select_target", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({x, y})
            });

            status.textContent = "Selected target: " + x + ", " + y;
        });

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const response = await fetch("/offer", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(pc.localDescription)
        });

        await pc.setRemoteDescription(await response.json());

        setInterval(refreshStatus, 200);
        refreshStatus();
    }

    start().catch((error) => {
        document.getElementById("status").textContent = error;
    });
    </script>
</body>
</html>
"""


async def webrtc_index(request):
    return web.Response(content_type="text/html", text=WEBRTC_HTML)


async def webrtc_offer(request):
    params = await request.json()

    pc = RTCPeerConnection()
    webrtc_pcs.add(pc)
    pc.addTrack(LatestFrameVideoTrack())

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info("WebRTC connection state: %s", pc.connectionState)
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await pc.close()
            webrtc_pcs.discard(pc)

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )


async def webrtc_select_target(request):
    global selected_click

    data = await request.json()
    x = float(data["x"])
    y = float(data["y"])

    with lock:
        selected_click = {"x": x, "y": y}

    return web.json_response({"ok": True, "x": x, "y": y})


async def webrtc_status(request):
    cmd = read_follow_command()
    age = time.monotonic() - cmd["updated_monotonic"]
    return web.json_response({
        "locked": cmd["target_locked"],
        "forward": cmd["forward_m_s"],
        "right": cmd["right_m_s"],
        "down": cmd["down_m_s"],
        "yaw": cmd["yaw_deg_s"],
        "source": cmd["source"],
        "age": age,
        "follow_real": FOLLOW_REAL,
    })


def run_webrtc_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    web_app = web.Application()
    web_app.router.add_get("/", webrtc_index)
    web_app.router.add_post("/offer", webrtc_offer)
    web_app.router.add_post("/select_target", webrtc_select_target)
    web_app.router.add_get("/status", webrtc_status)

    runner = web.AppRunner(web_app)
    loop.run_until_complete(runner.setup())

    site = web.TCPSite(runner, "0.0.0.0", 8080)
    loop.run_until_complete(site.start())

    logger.info("WebRTC follow safe streaming on http://0.0.0.0:8080")
    print("WebRTC follow safe streaming on http://0.0.0.0:8080")

    loop.run_forever()


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
      <head>
        <title>RealSense YOLO MJPEG Stream</title>
      </head>
      <body>
        <h2>RealSense YOLO MJPEG Stream</h2>
        <p>Click on a person in the image to select target.</p>

        <img id="video" src="/stream" width="640" style="cursor: crosshair; border: 1px solid #ccc;">

        <p id="status">No target selected</p>

        <script>
          const img = document.getElementById("video");
          const status = document.getElementById("status");

          img.addEventListener("click", function(event) {
            const rect = img.getBoundingClientRect();

            const scaleX = 640 / rect.width;
            const scaleY = 480 / rect.height;

            const x = (event.clientX - rect.left) * scaleX;
            const y = (event.clientY - rect.top) * scaleY;

            fetch("/select_target", {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify({ x: x, y: y })
            })
            .then(response => response.json())
            .then(data => {
              if (data.ok) {
                status.textContent = `Selected click: (${Math.round(x)}, ${Math.round(y)})`;
              } else {
                status.textContent = "Selection failed";
              }
            })
            .catch(err => {
              status.textContent = "Request error";
            });
          });
        </script>
      </body>
    </html>
    """


@app.route("/select_target", methods=["POST"])
def select_target():
    global selected_click

    data = request.get_json(silent=True) or {}
    x = data.get("x")
    y = data.get("y")

    if x is None or y is None:
        return jsonify({"ok": False, "error": "missing x or y"}), 400

    with lock:
        selected_click = {"x": float(x), "y": float(y)}

    return jsonify({"ok": True, "x": x, "y": y})


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

    follow_thread = threading.Thread(target=run_follow_control_loop, daemon=True)
    follow_thread.start()

    webrtc_thread = threading.Thread(target=run_webrtc_server, daemon=True)
    webrtc_thread.start()

    logger.info("WebRTC follow safe streaming on http://0.0.0.0:8080")
    print("WebRTC follow safe streaming on http://0.0.0.0:8080")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopped by user")

