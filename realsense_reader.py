import time
import threading
import os
import logging
from datetime import datetime

import pyrealsense2 as rs
import numpy as np


def setup_logger(name="stream"):
    log_dir = os.path.expanduser("~/follow_project/logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(
        log_dir,
        f"stream_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger


class RealSenseReader:
    def __init__(self, width=640, height=480, fps=30, timeout_ms=1000, max_lost=5):
        self.width = width
        self.height = height
        self.fps = fps
        self.timeout_ms = timeout_ms
        self.max_lost = max_lost

        self.pipeline = None
        self.config = None
        self.running = False

        self.frame = None
        self.frame_lock = threading.Lock()

        self.lost_count = 0
        self.restart_count = 0

        self.logger = setup_logger("realsense")
        self.logger.info("RealSenseReader initialized")

    def start_pipeline(self):
        self.logger.info("Starting RealSense pipeline...")
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(
            rs.stream.color,
            self.width,
            self.height,
            rs.format.bgr8,
            self.fps
        )
        self.pipeline.start(self.config)
        self.lost_count = 0
        self.logger.info("RealSense pipeline started successfully")

    def stop_pipeline(self):
        if self.pipeline is not None:
            try:
                self.pipeline.stop()
                self.logger.info("RealSense pipeline stopped")
            except Exception as e:
                self.logger.warning(f"Pipeline stop warning: {e}")
            finally:
                self.pipeline = None

    def restart_pipeline(self):
        self.restart_count += 1
        self.logger.warning(f"Restarting pipeline... count={self.restart_count}")
        self.stop_pipeline()
        time.sleep(2)
        try:
            self.start_pipeline()
            self.logger.info("Pipeline restarted successfully")
            return True
        except Exception as e:
            self.logger.error(f"Pipeline restart failed: {e}")
            return False

    def read_loop(self):
        self.running = True

        try:
            self.start_pipeline()
        except Exception as e:
            self.logger.error(f"Initial pipeline start failed: {e}")
            self.running = False
            return

        while self.running:
            try:
                frames = self.pipeline.wait_for_frames(timeout_ms=self.timeout_ms)
                color_frame = frames.get_color_frame()

                if not color_frame:
                    self.lost_count += 1
                    self.logger.warning(
                        f"WARNING camera lost: empty color frame, lost_count={self.lost_count}"
                    )
                else:
                    image = np.asanyarray(color_frame.get_data())
                    with self.frame_lock:
                        self.frame = image
                    self.lost_count = 0

            except Exception as e:
                self.lost_count += 1
                self.logger.warning(
                    f"WARNING camera lost: {e}, lost_count={self.lost_count}"
                )

            if self.lost_count >= self.max_lost:
                self.logger.warning("Camera considered lost, attempting recovery...")
                recovered = self.restart_pipeline()
                if recovered:
                    self.lost_count = 0
                else:
                    time.sleep(3)

        self.stop_pipeline()
        self.logger.info("Read loop exited cleanly")

    def get_frame(self):
        with self.frame_lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        self.running = False
        self.logger.info("Stopping RealSenseReader...")
