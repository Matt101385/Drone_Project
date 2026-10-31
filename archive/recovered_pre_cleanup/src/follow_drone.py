import time
import math
import atexit
import threading
import numpy as np
import pyrealsense2 as rs
import cv2
import os
import logging
from datetime import datetime
from hailo_person_detector import HailoPersonDetector
import asyncio
#from dataset_logger import maybe_capture

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame






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
print(f"[LOG] stream log: {log_file}", flush=True)

# =========================
# Basic Config
# =========================
WIDTH, HEIGHT, FPS = 640, 480, 30
FRAME_TIMEOUT_MS = 1000
MAX_LOST = 5
RESTART_WAIT_SEC = 2

MODEL_PATH = "yolo11n.pt"
CONF_THRES = 0.25

# yaw control
Kp = 20.0
DEADBAND = 0.06
MAX_YAW_CMD = 30.0

# forward distance control
TARGET_DIST_M = 2.0
DIST_DEADBAND = 0.30
Kp_forward = 0.65
MAX_FORWARD_CMD = 0.8
CAMERA_TILT_DEG = 30.0

# altitude hold in Offboard mode

DEPTH_MIN_M = 0.3
DEPTH_MAX_M = 10.0




latest_frame = None
latest_pitch_deg = 0.0
webrtc_pcs = set()
vision_lock = threading.Lock()
command_lock = threading.Lock()
selected_click = None
selected_target = None
pipeline = None
cfg = None
align = None
target_lost_count = 0
MAX_TARGET_LOST = 16

FOLLOW_REAL = os.environ.get("FOLLOW_REAL") == "1"
PX4_ADDR = os.environ.get("PX4_ADDR", "serial:///dev/serial0:921600")

FOLLOW_COMMAND_HZ = 10
FOLLOW_COMMAND_INTERVAL = 1.0 / FOLLOW_COMMAND_HZ

# Position Follow
POSITION_SETPOINT_HZ = 10.0
YAW_TELEMETRY_MAX_AGE_S = 1.0
POSITION_FOLLOW_LEASH_M = 1.00
POSITION_FOLLOW_YAW_LEASH_DEG = 30.0
MAX_DIRECT_FORWARD_OFFSET_M = 0.60
DIST_RATE_KD_S = 0.35
DIST_RATE_FILTER_ALPHA = 0.20
DIST_RATE_DEADBAND_M_S = 0.10

latest_follow_command = {
    "forward_m_s": 0.0,
    "distance_error_m": 0.0,
    "right_error_m": 0.0,
    "yaw_deg_s": 0.0,
    "target_locked": False,
    "source": "no-target",
    "control_mode": "DRY / VISION ONLY" if not FOLLOW_REAL else "PX4 CONNECTING",


    "updated_monotonic": time.monotonic(),
}
# =========================
# YOLO model
# =========================
try:
    model = HailoPersonDetector(conf_threshold=CONF_THRES)
    atexit.register(model.close)
    logger.info(f"Hailo YOLO11n loaded: {model.hef_path}")
    print(f"[HAILO] HEF: {model.hef_path}", flush=True)
except Exception as e:
    logger.error(f"Failed to load Hailo detector: {e}")
    print(f"[HAILO] detector load failed: {e}", flush=True)
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



def point_in_box(px, py, box):
    return box["x1"] <= px <= box["x2"] and box["y1"] <= py <= box["y2"]


def get_target_distance(depth_frame, cx, cy, box, win=5):
    x1 = int(box["x1"])
    y1 = int(box["y1"])
    x2 = int(box["x2"])
    y2 = int(box["y2"])

    box_w = max(x2 - x1, 1)
    box_h = max(y2 - y1, 1)

    # Sample the person's torso instead of only an 11x11
    # patch at the bounding-box center.
    roi_x1 = int(x1 + 0.30 * box_w)
    roi_x2 = int(x1 + 0.70 * box_w)
    roi_y1 = int(y1 + 0.20 * box_h)
    roi_y2 = int(y1 + 0.65 * box_h)

    samples = []

    # Skip pixels to keep CPU cost low.
    for py in range(roi_y1, roi_y2 + 1, 4):
        for px in range(roi_x1, roi_x2 + 1, 4):
            if (
                px < 0
                or py < 0
                or px >= WIDTH
                or py >= HEIGHT
            ):
                continue

            d = depth_frame.get_distance(px, py)

            if DEPTH_MIN_M <= d <= DEPTH_MAX_M:
                samples.append(d)

    # Do not trust a tiny number of surviving depth pixels.
    if len(samples) < 20:
        return None

    return float(np.median(samples))

def update_follow_command(
    forward_m_s,
    yaw_deg_s,
    target_locked,
    source,
    distance_error_m=0.0,
    right_error_m=0.0,
):
    with command_lock:
        latest_follow_command["forward_m_s"] = float(forward_m_s)
        latest_follow_command["distance_error_m"] = float(distance_error_m)
        latest_follow_command["right_error_m"] = float(right_error_m)
        latest_follow_command["yaw_deg_s"] = float(yaw_deg_s)
        latest_follow_command["target_locked"] = bool(target_locked)
        latest_follow_command["source"] = str(source)
        latest_follow_command["updated_monotonic"] = time.monotonic()


def read_follow_command():
    with command_lock:
        return dict(latest_follow_command)





async def watch_px4_state(drone, state):



    async def watch_local_position():
        async for pv in drone.telemetry.position_velocity_ned():
            state["north_m"] = float(pv.position.north_m)
            state["east_m"] = float(pv.position.east_m)
            state["down_m"] = float(pv.position.down_m)

    async def watch_attitude():
        global latest_pitch_deg
        async for attitude in drone.telemetry.attitude_euler():
            state["yaw_abs_deg"] = float(attitude.yaw_deg)
            state["yaw_updated_monotonic"] = time.monotonic()
            state["pitch_deg"] = float(attitude.pitch_deg)
            latest_pitch_deg = float(attitude.pitch_deg)



    await asyncio.gather(
        watch_local_position(),
        watch_attitude(),
    )





async def wait_until_connected(drone):
    print(f"[PX4] connecting to {PX4_ADDR} ...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[PX4] connected")
            return

async def watch_manual_override(
    drone,
    offboard_started_event,
    manual_override_event,
):
    from mavsdk.telemetry import FlightMode

    seen_offboard = False

    async for mode in drone.telemetry.flight_mode():
        # Do not monitor until our program has started Offboard.
        if not offboard_started_event.is_set():
            continue

        # Require seeing OFFBOARD at least once.
        # This avoids treating an old telemetry sample as manual override.
        if mode == FlightMode.OFFBOARD:
            seen_offboard = True
            continue

        # Only treat leaving OFFBOARD as manual override
        # after OFFBOARD has actually been observed.
        if seen_offboard:
            print(
                f"[MANUAL OVERRIDE] "
                f"flight mode changed from OFFBOARD to {mode}",
                flush=True,
            )
            manual_override_event.set()
            return



# ============================================================
# POSITION FOLLOW CORE
# ============================================================

def wrap_180(angle_deg):
    return (float(angle_deg) + 180.0) % 360.0 - 180.0


def wrap_360(angle_deg):
    return float(angle_deg) % 360.0


def yaw_telemetry_is_fresh(px4_state, now=None):
    yaw = px4_state.get("yaw_abs_deg")
    updated_at = px4_state.get("yaw_updated_monotonic")
    if yaw is None or updated_at is None:
        return False

    try:
        yaw = float(yaw)
        updated_at = float(updated_at)
    except (TypeError, ValueError):
        return False

    if not math.isfinite(yaw) or not math.isfinite(updated_at):
        return False

    if now is None:
        now = time.monotonic()

    age_s = now - updated_at
    return 0.0 <= age_s <= YAW_TELEMETRY_MAX_AGE_S


async def wait_for_local_pose(px4_state, timeout_s=5.0):
    start = time.monotonic()

    while True:
        values = (
            px4_state.get("north_m"),
            px4_state.get("east_m"),
            px4_state.get("down_m"),
            px4_state.get("yaw_abs_deg"),
        )

        if all(
            value is not None and math.isfinite(float(value))
            for value in values
        ) and yaw_telemetry_is_fresh(px4_state):
            return {
                "north_m": float(px4_state["north_m"]),
                "east_m": float(px4_state["east_m"]),
                "down_m": float(px4_state["down_m"]),
                "yaw_deg": wrap_360(px4_state["yaw_abs_deg"]),
            }

        if time.monotonic() - start > timeout_s:
            return None

        await asyncio.sleep(0.05)


def update_position_follow_status(px4_state, mode):
    with command_lock:
        latest_follow_command["control_mode"] = mode


async def position_setpoint_sender(
    drone,
    target,
    px4_state,
    manual_override_event,
    position_error_event,    prestream_stats=None,
):
    from mavsdk.offboard import PositionNedYaw

    interval = 1.0 / POSITION_SETPOINT_HZ

    # Diagnostic timing only.
    # Does not change N/E/D/Yaw control targets.
    last_send_start = None
    last_diag_print = time.monotonic()
    max_send_gap = 0.0
    max_call_duration = 0.0

    while not manual_override_event.is_set():
        send_start = time.monotonic()

        if last_send_start is not None:
            send_gap = send_start - last_send_start
            max_send_gap = max(
                max_send_gap,
                send_gap,
            )

        last_send_start = send_start

        try:
            await drone.offboard.set_position_ned(
                PositionNedYaw(
                    float(target["north_m"]),
                    float(target["east_m"]),
                    float(target["down_m"]),
                    float(target["yaw_deg"]),
                )
            )

            call_duration = (
                time.monotonic() - send_start
            )

            max_call_duration = max(
                max_call_duration,
                call_duration,
            )

            if prestream_stats is not None: prestream_stats["success_count"] = prestream_stats.get("success_count", 0) + 1; prestream_stats["first_success_at"] = prestream_stats.get("first_success_at") or time.monotonic(); prestream_stats["last_success_at"] = time.monotonic()
        except Exception as exc:
            print(
                f"[POSITION] set_position_ned failed: {exc}",
                flush=True,
            )
            position_error_event.set()
            return

        update_position_follow_status(
            px4_state,
            target["mode"],
        )

        now = time.monotonic()

        if now - last_diag_print >= 5.0:
            print(
                "[SETPOINT TIMING] "
                f"max_gap="
                f"{max_send_gap * 1000:.1f} ms | "
                f"max_call="
                f"{max_call_duration * 1000:.1f} ms",
                flush=True,
            )

            max_send_gap = 0.0
            max_call_duration = 0.0
            last_diag_print = now

        await asyncio.sleep(interval)


async def position_follow_loop(
    target,
    px4_state,
    manual_override_event,
    position_error_event,
):
    print(
        "\n"
        "========================================\n"
        "POSITION FOLLOW ACTIVE\n"
        "Vision updates N/E/Yaw position targets.\n"
        "Down position remains fixed.\n"
        "PX4 controls the aircraft position.\n"
        "========================================",
        flush=True,
    )

    fixed_down_m = float(target["down_m"])

    hold_latched = False

    last_time = time.monotonic()
    last_print = 0.0

    while (
        not manual_override_event.is_set()
        and not position_error_event.is_set()
    ):
        now = time.monotonic()

        dt = min(
            max(now - last_time, 0.0),
            0.20,
        )
        last_time = now

        cmd = read_follow_command()
        age = now - cmd["updated_monotonic"]

        actual_n = px4_state.get("north_m")
        actual_e = px4_state.get("east_m")
        actual_yaw = px4_state.get("yaw_abs_deg")

        target_locked = (
            cmd["target_locked"]
            and age <= 0.5
            and actual_n is not None
            and actual_e is not None
            and actual_yaw is not None
        )

        if not target_locked:
            prev_forward_distance_m = None
            prev_distance_rate_time = None
            filtered_distance_rate_m_s = 0.0
        if target_locked:
            hold_latched = False
            # ------------------------------------------------
            # FORWARD GUIDANCE -> MOVING POSITION TARGET
            # ------------------------------------------------
            heading_rad = math.radians(float(actual_yaw))

            forward_offset_m = max(
                -MAX_DIRECT_FORWARD_OFFSET_M,
                min(
                    MAX_DIRECT_FORWARD_OFFSET_M,
                    float(cmd["distance_error_m"]),
                ),
            )
            right_offset_m = float(cmd["right_error_m"])

            proposed_n = float(actual_n) + forward_offset_m * math.cos(heading_rad) - right_offset_m * math.sin(heading_rad)
            proposed_e = float(actual_e) + forward_offset_m * math.sin(heading_rad) + right_offset_m * math.cos(heading_rad)

            # ------------------------------------------------
            # POSITION LEASH
            # ------------------------------------------------
            leash_n = proposed_n - float(actual_n)
            leash_e = proposed_e - float(actual_e)

            leash_distance = math.hypot(
                leash_n,
                leash_e,
            )

            if leash_distance > POSITION_FOLLOW_LEASH_M:
                scale = (
                    POSITION_FOLLOW_LEASH_M
                    / leash_distance
                )

                proposed_n = (
                    float(actual_n)
                    + leash_n * scale
                )

                proposed_e = (
                    float(actual_e)
                    + leash_e * scale
                )

            target["north_m"] = proposed_n
            target["east_m"] = proposed_e

            # ------------------------------------------------
            # YAW GUIDANCE -> MOVING YAW POSITION TARGET
            # ------------------------------------------------
            proposed_yaw = wrap_360(
                float(target["yaw_deg"])
                + float(cmd["yaw_deg_s"]) * dt
            )

            yaw_error = wrap_180(
                proposed_yaw - float(actual_yaw)
            )

            yaw_error = max(
                -POSITION_FOLLOW_YAW_LEASH_DEG,
                min(
                    POSITION_FOLLOW_YAW_LEASH_DEG,
                    yaw_error,
                ),
            )

            target["yaw_deg"] = wrap_360(
                float(actual_yaw) + yaw_error
            )

            # Height remains locked to the position
            # sampled when Position Follow starts.
            target["down_m"] = fixed_down_m

            target["mode"] = (
                "POSITION FOLLOW / TARGET LOCKED"
            )

        else:
            if (
                not hold_latched
                and actual_n is not None
                and actual_e is not None
            ):
                target["north_m"] = float(actual_n)
                target["east_m"] = float(actual_e)
                hold_latched = True

            target["down_m"] = fixed_down_m

            target["mode"] = (
                "POSITION FOLLOW / HOLD - NO TARGET"
            )

        if now - last_print >= 1.0:
            print(
                "[POSITION FOLLOW] "
                f"locked={target_locked} | "
                f"N={target['north_m']:+.2f} "
                f"E={target['east_m']:+.2f} "
                f"D={target['down_m']:+.2f} "
                f"Yaw={target['yaw_deg']:.1f}",
                flush=True,
            )
            last_print = now

        await asyncio.sleep(
            1.0 / POSITION_SETPOINT_HZ
        )


async def follow_control_loop():
    # --------------------------------------------------------
    # DRY MODE
    # Vision continues to run, but nothing is sent to PX4.
    # --------------------------------------------------------
    if not FOLLOW_REAL:
        print(
            "[DRY] FOLLOW_REAL is not 1; "
            "vision runs, Pixhawk commands are not sent.",
            flush=True,
        )

        with command_lock:
            latest_follow_command["control_mode"] = (
                "DRY / VISION ONLY"
            )

        last_print = 0.0

        while True:
            cmd = read_follow_command()
            now = time.monotonic()

            if now - last_print >= 1.0:
                print(
                    "[DRY] "
                    f"locked={cmd['target_locked']} "
                    f"forward_guidance={cmd['forward_m_s']:+.2f} "
                    f"yaw_guidance={cmd['yaw_deg_s']:+.1f} "
                    f"source={cmd['source']} "
                    f"age={now - cmd['updated_monotonic']:.2f}s",
                    flush=True,
                )
                last_print = now

            await asyncio.sleep(0.1)

    # --------------------------------------------------------
    # REAL POSITION FOLLOW
    # --------------------------------------------------------
    print("[PX4] importing mavsdk...", flush=True)

    from mavsdk import System
    from mavsdk.offboard import OffboardError, PositionNedYaw

    print("[PX4] mavsdk imported", flush=True)

    drone = System()

    print("[PX4] System created", flush=True)
    print(
        f"[PX4] calling connect: {PX4_ADDR}",
        flush=True,
    )

    await drone.connect(
        system_address=PX4_ADDR
    )

    print("[PX4] connect returned", flush=True)

    await wait_until_connected(drone)

    with command_lock:
        latest_follow_command["control_mode"] = (
            "PX4 CONNECTED / WAITING LOCAL POSE"
        )

    # --------------------------------------------------------
    # Events
    # --------------------------------------------------------
    offboard_started_event = asyncio.Event()
    manual_override_event = asyncio.Event()
    position_error_event = asyncio.Event()

    # --------------------------------------------------------
    # PX4 state
    # --------------------------------------------------------
    px4_state = {

        # Local NED position
        "north_m": None,
        "east_m": None,
        "down_m": None,

        # Yaw
        "yaw_abs_deg": None,
        "yaw_updated_monotonic": None,
        "pitch_deg": None,
    }

    manual_override_task = asyncio.create_task(
        watch_manual_override(
            drone,
            offboard_started_event,
            manual_override_event,
        )
    )

    px4_state_task = asyncio.create_task(
        watch_px4_state(
            drone,
            px4_state,
        )
    )

    sender_task = None
    offboard_active = False

    try:
        # ----------------------------------------------------
        # POSITION ENTRY
        #
        # Sample the aircraft's CURRENT local pose.
        # That exact pose becomes the first Offboard target.
        # ----------------------------------------------------
        current_pose = await wait_for_local_pose(
            px4_state,
            timeout_s=5.0,
        )

        if current_pose is None:
            print(
                "[POSITION] No valid local N/E/D/Yaw pose. "
                "Refusing to enter Offboard.",
                flush=True,
            )

            with command_lock:
                latest_follow_command["control_mode"] = (
                    "POSITION BLOCKED / NO LOCAL POSE"
                )

            return

        target = {
            "north_m": current_pose["north_m"],
            "east_m": current_pose["east_m"],
            "down_m": current_pose["down_m"],
            "yaw_deg": current_pose["yaw_deg"],
            "mode": "POSITION FOLLOW / HOLD",
        }

        print(
            "[POSITION] Initial target = current pose | "
            f"N={target['north_m']:+.2f} "
            f"E={target['east_m']:+.2f} "
            f"D={target['down_m']:+.2f} "
            f"Yaw={target['yaw_deg']:.1f}",
            flush=True,
        )

        with command_lock:
            latest_follow_command["control_mode"] = (
                "POSITION HOLD / ENTERING OFFBOARD"
            )


        print("[OFFBOARD] Starting 10 Hz setpoint prestream...", flush=True)

        sender_task = asyncio.create_task(position_setpoint_sender(drone, target, px4_state, manual_override_event, position_error_event))

        await asyncio.sleep(1.5)

        if position_error_event.is_set():
            print("[OFFBOARD] Prestream failed. Refusing Offboard.", flush=True)
            return

        print("[OFFBOARD] Prestream complete. Requesting Offboard...", flush=True)

        try:
            await drone.offboard.start()
        except OffboardError as exc:
            print(f"[PX4] Offboard start failed: {exc}", flush=True)
            with command_lock:
                latest_follow_command["control_mode"] = "OFFBOARD START FAILED"
            return

        offboard_active = True
        offboard_started_event.set()

        print("[PX4] OFFBOARD POSITION active.", flush=True)




        print(
            "[PX4] Current D is now the fixed "
            "Position Follow height target.",
            flush=True,
        )



        # ----------------------------------------------------
        # POSITION FOLLOW
        #
        # No valid target:
        #     hold last N/E/D/Yaw position target.
        #
        # Valid target:
        #     forward guidance -> moving N/E target
        #     yaw guidance     -> moving Yaw target
        #
        # D remains fixed.
        # ----------------------------------------------------
        await position_follow_loop(
            target,
            px4_state,
            manual_override_event,
            position_error_event,
        )

        if position_error_event.is_set():
            print(
                "[POSITION] Follow stopped because "
                "Position setpoint transmission failed.",
                flush=True,
            )

    finally:
        # ----------------------------------------------------
        # Stop sender first so cleanup cannot emit another
        # Position setpoint after manual override.
        # ----------------------------------------------------
        if sender_task is not None:
            sender_task.cancel()

            try:
                await sender_task
            except asyncio.CancelledError:
                pass

        # ----------------------------------------------------
        # RC/manual override has priority.
        # Do not send another Offboard command after it.
        # ----------------------------------------------------
        if manual_override_event.is_set():
            print(
                "[PX4] cleanup: Manual Override detected; "
                "no further Offboard command will be sent.",
                flush=True,
            )

            manual_override_task.cancel()

            try:
                await manual_override_task
            except asyncio.CancelledError:
                pass

        else:
            # Cancel watcher BEFORE our own offboard.stop()
            # so our intentional stop is not classified as
            # an RC manual override.
            manual_override_task.cancel()

            try:
                await manual_override_task
            except asyncio.CancelledError:
                pass

            if offboard_active:
                print(
                    "[PX4] cleanup: stopping Offboard.",
                    flush=True,
                )

                try:
                    await drone.offboard.stop()
                except Exception as exc:
                    print(
                        f"[PX4] Offboard stop warning: {exc}",
                        flush=True,
                    )

        px4_state_task.cancel()

        try:
            await px4_state_task
        except asyncio.CancelledError:
            pass

def run_follow_control_loop():
    print("[PX4] thread started", flush=True)
    try:
        asyncio.run(follow_control_loop())
    except Exception as e:
        print("[PX4] thread crashed:", repr(e), flush=True)

# =========================
# Camera Loop
# =========================
def camera_loop():
    global latest_frame, selected_click, selected_target, target_lost_count

    lost_count = 0
    frame_count = 0
    fps_est = 0.0
    last_t = time.time()
    prev_forward_distance_m = None
    prev_distance_rate_time = None
    filtered_distance_rate_m_s = 0.0

    try:
        start_pipeline()
    except Exception as e:
        logger.error(f"Initial pipeline start failed: {e}")
        return

    while True:
        try:
            if pipeline is None:
                logger.warning("Pipeline is None, attempting restart")
                recovered = restart_pipeline()
                if not recovered:
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
                        time.sleep(1)
                    continue

                time.sleep(0.05)
                continue

            color_image = np.asanyarray(color_frame.get_data())
            #dataset_frame = color_image.copy()

            # ===== YOLO detection =====
            detect_start = time.time()
            det_count = 0
            person_boxes = []
            locked_target = None

            if model is not None:
                try:
                    people = model.detect(color_image)
                    det_count = len(people)

                    model._debug_count = getattr(model, "_debug_count", 0) + 1
                    if model._debug_count % 30 == 0:
                        print(
                            f"[HAILO DEBUG] people={len(people)} "
                            f"first={people[:1]}",
                            flush=True,
                        )

                    for person in people:
                        conf = float(person["confidence"])
                        x1 = int(person["x1"])
                        y1 = int(person["y1"])
                        x2 = int(person["x2"])
                        y2 = int(person["y2"])

                        label = f"person {conf:.2f}"
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
                        cv2.rectangle(
                            color_image,
                            (x1, y1),
                            (x2, y2),
                            color,
                            2,
                        )
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
                    logger.warning(f"Hailo inference failed: {e}")
                    print(
                        f"[HAILO ERROR] {type(e).__name__}: {e}",
                        flush=True,
                    )


            with vision_lock:
                click = dict(selected_click) if selected_click is not None else None

            # ===== click-select target =====
            if click is not None and len(person_boxes) > 0:
                hit_boxes = [
                    b for b in person_boxes
                    if point_in_box(click["x"], click["y"], b)
                ]
                if len(hit_boxes) > 0:
                    locked_target = min(hit_boxes, key=lambda b: b["area"])
                    with vision_lock:
                        selected_target = dict(locked_target)
                        selected_click = None

            # keep selected target across frames
            if locked_target is None:
                with vision_lock:
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
                        with vision_lock:

                            selected_target = dict(locked_target)
                        target_lost_count = 0
                    else:
                        target_lost_count += 1

                elif prev_target is not None:
                    target_lost_count += 1

                if target_lost_count >= MAX_TARGET_LOST:
                    with vision_lock:
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
            forward_distance_m = None


            target_cx = None
            target_cy = None
            bbox_h_pct = None
            bbox_cx_pct = None
            bbox_cy_pct = None
            bbox_bottom_pct = None

            if locked_target is not None:
                x1 = locked_target["x1"]
                y1 = locked_target["y1"]
                x2 = locked_target["x2"]
                y2 = locked_target["y2"]
                target_cx = locked_target["cx"]
                target_cy = locked_target["cy"]
                frame_h, frame_w = color_image.shape[:2]
                bbox_h_pct = 100.0 * (y2 - y1) / frame_h
                bbox_cx_pct = 100.0 * target_cx / frame_w
                bbox_cy_pct = 100.0 * target_cy / frame_h
                bbox_bottom_pct = 100.0 * y2 / frame_h
                target_dist = get_target_distance(depth_frame, target_cx, target_cy, locked_target, win=5)

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

                distance_error_m = 0.0
                right_error_m = 0.0

                if target_dist is not None:
                    intrin = depth_frame.profile.as_video_stream_profile().intrinsics
                    point = rs.rs2_deproject_pixel_to_point(intrin, [float(target_cx), float(target_cy)], float(target_dist))
                    cam_x = float(point[0])
                    cam_y = float(point[1])
                    cam_z = float(point[2])
                    right_error_m = cam_x
                    tilt_rad = math.radians(CAMERA_TILT_DEG)
                    pitch_rad = math.radians(float(latest_pitch_deg))
                    body_forward_m = cam_z * math.cos(tilt_rad) - cam_y * math.sin(tilt_rad)
                    body_down_m = cam_z * math.sin(tilt_rad) + cam_y * math.cos(tilt_rad)
                    forward_distance_m = body_forward_m * math.cos(pitch_rad) + body_down_m * math.sin(pitch_rad)

                    rate_now = time.monotonic()

                    if prev_forward_distance_m is not None and prev_distance_rate_time is not None:
                        rate_dt = rate_now - prev_distance_rate_time

                        if 0.02 <= rate_dt <= 0.25:
                            raw_distance_rate_m_s = (forward_distance_m - prev_forward_distance_m) / rate_dt
                            filtered_distance_rate_m_s = (1.0 - DIST_RATE_FILTER_ALPHA) * filtered_distance_rate_m_s + DIST_RATE_FILTER_ALPHA * raw_distance_rate_m_s
                        else:
                            filtered_distance_rate_m_s = 0.0
                    prev_forward_distance_m = forward_distance_m
                    prev_distance_rate_time = rate_now

                    dist_error = forward_distance_m - TARGET_DIST_M
                    #print(f"[DIST] raw={target_dist:.2f}m forward={forward_distance_m:.2f}m error={dist_error:.2f}m")
                    if abs(dist_error) < DIST_DEADBAND:
                        position_error_m = 0.0
                    else:
                        position_error_m = dist_error

                    if filtered_distance_rate_m_s < -DIST_RATE_DEADBAND_M_S:
                        braking_rate_m_s = filtered_distance_rate_m_s
                    else:
                        braking_rate_m_s = 0.0

                    distance_error_m = position_error_m + DIST_RATE_KD_S * braking_rate_m_s

                    forward_cmd = Kp_forward * distance_error_m
                    forward_cmd = max(min(forward_cmd, MAX_FORWARD_CMD), -MAX_FORWARD_CMD)

                target_locked = (
                    locked_target is not None
                    and target_dist is not None
                )
                update_follow_command(
                    forward_m_s=float(
                        forward_cmd if target_locked else 0.0
                    ),
                    yaw_deg_s=float(
                        yaw_cmd if target_locked else 0.0
                    ),
                    target_locked=target_locked,
                    source="pi-vision-11",
                    distance_error_m=float(
                        distance_error_m if target_locked else 0.0
                    ),
                    right_error_m=float(
                        right_error_m if target_locked else 0.0
                    ),
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
                    yaw_deg_s=0.0,
                    target_locked=False,
                    source="no-target",
                    right_error_m=0.0,
                )
            infer_ms = (time.time() - detect_start) * 1000.0
            #maybe_capture(dataset_frame, locals())

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
                    f"locked {locked_target is not None}, "
                    f"dist {target_dist if target_dist is not None else 'N/A'}, "
                    f"dist_error {dist_error:.2f}, "
                    f"forward_cmd {forward_cmd:.3f}, "
                    f"yaw_cmd {yaw_cmd:.3f}, infer {infer_ms:.1f} ms"
                )

            # Minimal flight-video overlay.
            overlay_state = (
                "LOCKED"
                if locked_target is not None
                else "SEARCHING"
            )

            cv2.putText(
                color_image,
                overlay_state,
                (12, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
            )

            if target_dist is not None: cv2.putText(color_image, f"RAW {target_dist:.2f} m", (12, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            if forward_distance_m is not None: cv2.putText(color_image, f"HORIZ {forward_distance_m:.2f} m", (12, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            cv2.putText(color_image, f"PITCH {latest_pitch_deg:+.1f} deg", (12, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.putText(color_image, f"FWD {forward_cmd:+.2f} m/s", (12, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            if bbox_h_pct is not None: cv2.putText(color_image, f"BBOX H {bbox_h_pct:.0f}%  Y {bbox_cy_pct:.0f}%", (12, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            if bbox_cx_pct is not None: cv2.putText(color_image, f"BBOX X {bbox_cx_pct:.0f}%  BOT {bbox_bottom_pct:.0f}%", (12, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            cv2.putText(color_image, f"D-RATE {filtered_distance_rate_m_s:+.2f} m/s", (12, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            with vision_lock:
                latest_frame = color_image.copy()



        except Exception as e:
            logger.error(f"Main loop unexpected error: {e}")
            time.sleep(0.1)
            continue



class LatestFrameVideoTrack(VideoStreamTrack):
    async def recv(self):
        pts, time_base = await self.next_timestamp()

        while True:
            with vision_lock:
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
    <video id="video" autoplay playsinline muted
           style="width:100%;background:#000;cursor:crosshair;"></video>

    <div id="status"
         style="margin-top:10px;color:#888;font-size:14px;">
        Connecting...
    </div>

    <div style="
        margin-top:12px;
        background:#181818;
        border:1px solid #333;
        border-radius:8px;
        padding:12px 14px;
        line-height:1.55;
        color:#d5d5d5;
    ">
        <div style="
            font-size:15px;
            font-weight:700;
            letter-spacing:0.08em;
            margin-bottom:8px;
        ">
            POSITION FOLLOW
        </div>

        <div>
            Control:
            <span id="controlMode">UNKNOWN</span>
        </div>

        <div>
            Architecture:
            PositionNedYaw
        </div>

        <div>
            Height:
            Hold D from Follow entry
        </div>

        <div>
            Position Leash:
            1.00 m
        </div>

        <div>
            Yaw Leash:
            &plusmn;30&deg;
        </div>

        <div style="margin-top:6px;color:#999;">
            No valid target &rarr; hold last N/E/D/Yaw target
        </div>
    </div>
  </section>

        <aside style="background:#1d1d1d;border:1px solid #444;border-radius:8px;padding:14px;font-size:18px;line-height:1.55;">
            <div>Mode: <span id="mode">DRY</span></div>
            <div>Locked: <span id="locked" style="color:#ff5555;">False</span></div>
            <div>Forward Guidance: <span id="forward" style="color:#ffd84d;">+0.00</span> m/s</div>
            <div>Yaw Guidance: <span id="yaw" style="color:#ffd84d;">+0.0</span> deg/s</div>
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
            document.getElementById("yaw").textContent = signed(s.yaw, 1);
            document.getElementById("source").textContent = s.source;
            document.getElementById("age").textContent = Number(s.age).toFixed(2);

            document.getElementById("controlMode").textContent =
                s.control_mode || "UNKNOWN";
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

    with vision_lock:
        selected_click = {"x": x, "y": y}

    return web.json_response({"ok": True, "x": x, "y": y})


async def webrtc_status(request):
    cmd = read_follow_command()
    age = time.monotonic() - cmd["updated_monotonic"]
    return web.json_response({
        "locked": cmd["target_locked"],
        "forward": cmd["forward_m_s"],
        "yaw": cmd["yaw_deg_s"],
        "source": cmd["source"],
        "age": age,

        # PX4 altitude / vertical debug status
        "control_mode": cmd["control_mode"],
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

