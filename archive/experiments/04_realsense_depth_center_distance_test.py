import pyrealsense2 as rs
import numpy as np
import cv2
import time

def center_distance_m(depth_frame, cx, cy, r=4):
    import numpy as np
    depth_image = np.asanyarray(depth_frame.get_data())

    y1, y2 = max(0, cy-r), min(depth_image.shape[0], cy+r+1)
    x1, x2 = max(0, cx-r), min(depth_image.shape[1], cx+r+1)

    roi = depth_image[y1:y2, x1:x2].reshape(-1)
    roi = roi[roi > 0]  # 去掉无效值

    if roi.size == 0:
        return 0.0

    scale = depth_frame.get_units()
    return float(np.median(roi) * scale)
def main():
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    pipeline.start(config)

    align = rs.align(rs.stream.color)

    # 每隔多少帧保存一次图片（你可以改成 30=约1秒一次）
    SAVE_EVERY_N_FRAMES = 30

    try:
        i = 0
        while True:
            frames = pipeline.wait_for_frames()
            aligned = align.process(frames)

            depth_frame = aligned.get_depth_frame()
            color_frame = aligned.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # 中心点距离（米）
            h, w = depth_image.shape
            cx, cy = w // 2, h // 2
            dist_m = center_distance_m(depth_frame, cx, cy)

            # 终端打印（实时验证）
            print(f"frame={i:06d}  center_distance={dist_m:.2f} m")

            # 深度可视化（保存用）
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )

            # 在彩色图上画十字和距离（保存用）
            cv2.drawMarker(color_image, (cx, cy), (0, 255, 0),
                           markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
            cv2.putText(color_image, f"{dist_m:.2f} m", (cx + 10, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 每隔N帧保存一次（color.jpg / depth.jpg会不断刷新）
            if i % SAVE_EVERY_N_FRAMES == 0:
                cv2.imwrite("color.jpg", color_image)
                cv2.imwrite("depth.jpg", depth_colormap)

            i += 1
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")

    finally:
        pipeline.stop()

if __name__ == "__main__":
    main()
