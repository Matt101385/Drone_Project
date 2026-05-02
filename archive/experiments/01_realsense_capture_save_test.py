import time
import numpy as np
import pyrealsense2 as rs
import cv2

def main():
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    pipeline.start(config)
    print("✅ RealSense started. Capturing 60 frames...")

    t0 = time.time()
    frame_count = 0
    last_img = None

    try:
        for _ in range(60):
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            last_img = np.asanyarray(color_frame.get_data())
            frame_count += 1

        dt = time.time() - t0
        if frame_count == 0:
            raise RuntimeError("No frames captured")

        fps = frame_count / dt
        out = "/home/matt/follow_project/realsense_color.jpg"
        cv2.imwrite(out, last_img)
        print(f"✅ Captured {frame_count} frames in {dt:.2f}s (FPS≈{fps:.1f})")
        print(f"✅ Saved last frame to: {out}")

    finally:
        pipeline.stop()
        print("✅ RealSense stopped.")

if __name__ == "__main__":
    main()
