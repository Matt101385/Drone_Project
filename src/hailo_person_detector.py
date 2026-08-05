from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from hailo_apps.python.core.common.hailo_inference import HailoInfer
from hailo_apps.python.core.common.toolbox import default_preprocess
from hailo_apps.python.standalone_apps.object_detection.object_detection_post_process import (
    extract_detections,
)


class HailoPersonDetector:
    """Synchronous person detector backed by a Hailo YOLO11n HEF.

    Input:
        OpenCV BGR uint8 frame, shape HxWx3.

    Output:
        A list of dictionaries in original-frame pixel coordinates:
        {"x1": int, "y1": int, "x2": int, "y2": int,
         "confidence": float, "class_id": 0}
    """

    PERSON_CLASS_ID = 0

    def __init__(
        self,
        hef_path: str | os.PathLike[str] | None = None,
        conf_threshold: float = 0.25,
        max_detections: int = 100,
        timeout_ms: int = 10_000,
    ) -> None:
        if not 0.0 <= conf_threshold <= 1.0:
            raise ValueError("conf_threshold must be between 0 and 1")
        if max_detections < 1:
            raise ValueError("max_detections must be at least 1")
        if timeout_ms < 1:
            raise ValueError("timeout_ms must be positive")

        self.hef_path = self._resolve_hef_path(hef_path)
        self.conf_threshold = float(conf_threshold)
        self.max_detections = int(max_detections)
        self.timeout_ms = int(timeout_ms)

        # Initialize once, then reuse for every frame.
        self._infer = HailoInfer(str(self.hef_path), batch_size=1)
        input_shape = tuple(int(v) for v in self._infer.get_input_shape())
        if len(input_shape) != 3 or input_shape[2] != 3:
            self._infer.close()
            raise RuntimeError(
                f"Unexpected HEF input shape {input_shape}; expected HxWx3"
            )

        self.model_height, self.model_width, _ = input_shape
        self._config_data = {
            "visualization_params": {
                "score_thres": self.conf_threshold,
                "max_boxes_to_draw": self.max_detections,
            }
        }
        self._lock = threading.Lock()
        self._closed = False

    @staticmethod
    def _resolve_hef_path(
        hef_path: str | os.PathLike[str] | None,
    ) -> Path:
        """Resolve yolov11n.hef without changing the project directory layout."""
        if hef_path is not None:
            path = Path(hef_path).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(f"HEF file not found: {path}")
            return path

        for env_name in (
            "HAILO_YOLO11N_HEF",
            "HAILO_HEF_PATH",
            "YOLOV11N_HEF",
        ):
            value = os.environ.get(env_name)
            if value:
                path = Path(value).expanduser().resolve()
                if path.is_file():
                    return path

        candidates = [
            Path.cwd() / "yolov11n.hef",
            Path.cwd() / "models" / "yolov11n.hef",
            Path(__file__).resolve().parent / "yolov11n.hef",
            Path(__file__).resolve().parent / "models" / "yolov11n.hef",
            Path("/usr/local/hailo/resources/models/hailo10h/yolov11n.hef"),
            Path("/usr/local/hailo/resources/models/yolov11n.hef"),
            Path("/usr/local/hailo/resources/hefs/hailo10h/yolov11n.hef"),
            Path("/usr/local/hailo/resources/hefs/yolov11n.hef"),
            Path("/usr/local/hailo/resources/yolov11n.hef"),
        ]
        for path in candidates:
            if path.is_file():
                return path.resolve()

        resource_root = Path("/usr/local/hailo/resources")
        if resource_root.is_dir():
            matches = sorted(resource_root.rglob("yolov11n.hef"))
            if matches:
                return matches[0].resolve()

        raise FileNotFoundError(
            "Could not find yolov11n.hef. Pass hef_path explicitly or set "
            "HAILO_YOLO11N_HEF. Locate it with: "
            "find /usr/local/hailo/resources -type f -name 'yolov11n.hef'"
        )

    @staticmethod
    def _clone_hailo_output(value: Any) -> Any:
        """Recursively copy Hailo output without forcing ragged NMS data
        into one homogeneous NumPy array.
        """
        if isinstance(value, np.ndarray):
            return value.copy()

        if isinstance(value, list):
            return [
                HailoPersonDetector._clone_hailo_output(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return tuple(
                HailoPersonDetector._clone_hailo_output(item)
                for item in value
            )

        if isinstance(value, dict):
            return {
                key: HailoPersonDetector._clone_hailo_output(item)
                for key, item in value.items()
            }

        return value

    @staticmethod
    def _copy_output_from_bindings(bindings: Any) -> Any:
        """Copy inference output while callback bindings remain valid."""
        output_names = list(bindings._output_names)

        if len(output_names) == 1:
            raw_output = bindings.output().get_buffer()
            return HailoPersonDetector._clone_hailo_output(raw_output)

        return {
            name: HailoPersonDetector._clone_hailo_output(
                bindings.output(name).get_buffer()
            )
            for name in output_names
        }

    def detect(self, frame_bgr: np.ndarray) -> list[dict[str, int | float]]:
        """Detect people in one BGR frame and return original-image boxes."""
        if self._closed:
            raise RuntimeError("HailoPersonDetector is already closed")
        if not isinstance(frame_bgr, np.ndarray):
            raise TypeError("frame_bgr must be a numpy.ndarray")
        if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
            raise ValueError(
                f"frame_bgr must have shape HxWx3; got {frame_bgr.shape}"
            )
        if frame_bgr.dtype != np.uint8:
            raise ValueError(
                f"frame_bgr must use uint8 pixels; got {frame_bgr.dtype}"
            )
        if frame_bgr.size == 0:
            raise ValueError("frame_bgr is empty")

        # RealSense/OpenCV supplies BGR; Hailo's official standalone path uses RGB.
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        model_input = default_preprocess(
            frame_rgb,
            self.model_width,
            self.model_height,
        )
        model_input = np.ascontiguousarray(model_input, dtype=np.uint8)

        completion_event = threading.Event()
        callback_result: dict[str, Any] = {}

        def inference_callback(completion_info: Any, bindings_list: list[Any]) -> None:
            try:
                if completion_info.exception:
                    callback_result["error"] = RuntimeError(
                        f"Hailo inference failed: {completion_info.exception}"
                    )
                else:
                    callback_result["output"] = self._copy_output_from_bindings(
                        bindings_list[0]
                    )
            except Exception as exc:
                callback_result["error"] = exc
            finally:
                completion_event.set()

        # Serialize calls because this wrapper exposes a synchronous API.
        with self._lock:
            job = self._infer.run([model_input], inference_callback)
            job.wait(self.timeout_ms)
            if not completion_event.wait(self.timeout_ms / 1000.0):
                raise TimeoutError(
                    f"Hailo callback did not complete within {self.timeout_ms} ms"
                )

        if "error" in callback_result:
            raise callback_result["error"]
        if "output" not in callback_result:
            raise RuntimeError("Hailo inference completed without an output buffer")

        detections = extract_detections(
            frame_rgb,
            callback_result["output"],
            self._config_data,
        )

        frame_height, frame_width = frame_bgr.shape[:2]
        people: list[dict[str, int | float]] = []

        for box, class_id, score in zip(
            detections["detection_boxes"],
            detections["detection_classes"],
            detections["detection_scores"],
        ):
            if int(class_id) != self.PERSON_CLASS_ID:
                continue

            x1, y1, x2, y2 = (int(round(float(v))) for v in box)
            x1 = max(0, min(x1, frame_width - 1))
            y1 = max(0, min(y1, frame_height - 1))
            x2 = max(0, min(x2, frame_width - 1))
            y2 = max(0, min(y2, frame_height - 1))

            if x2 <= x1 or y2 <= y1:
                continue

            people.append(
                {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": float(score),
                    "class_id": self.PERSON_CLASS_ID,
                }
            )

        people.sort(key=lambda item: float(item["confidence"]), reverse=True)
        return people

    def close(self) -> None:
        if self._closed:
            return
        with self._lock:
            self._infer.close()
            self._closed = True

    def __enter__(self) -> "HailoPersonDetector":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()
