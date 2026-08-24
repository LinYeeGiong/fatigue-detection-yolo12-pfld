import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from server.domain.fatigue import FatigueClassifier, Observation


class OnnxDetector:
    name = "YOLO11-face + PFLD (ONNX)"
    ready = True

    def __init__(self, model_dir: Path, device_preference: str = "auto"):
        model_dir = Path(model_dir)
        available = ort.get_available_providers()
        use_cuda = device_preference != "cpu" and "CUDAExecutionProvider" in available
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if use_cuda else ["CPUExecutionProvider"]
        self.device = "cuda" if use_cuda else "cpu"
        self.face_session = ort.InferenceSession(str(model_dir / "yolo11_face.onnx"), providers=providers)
        self.pfld_session = ort.InferenceSession(str(model_dir / "pfpld.onnx"), providers=providers)
        self.classifier = FatigueClassifier(window_seconds=60)

    def detect_image(self, content: bytes, filename: str) -> dict:
        image = self._decode(content)
        faces = self._detect_faces(image)
        details = [self._landmark_metrics(image, box) for box in faces]
        details = [item for item in details if item is not None]
        if not details:
            return self._result(filename, 0, None, "normal", [], 0)
        metrics = details[0]
        events = self._events(metrics)
        level = "moderate" if len(events) >= 2 else "mild" if events else "normal"
        score = {"normal": 10, "mild": 45, "moderate": 70}[level]
        return self._result(filename, len(details), metrics, level, events, score)

    def detect_frame(self, content: bytes) -> dict:
        image = self._decode(content)
        faces = self._detect_faces(image)
        details = [self._landmark_metrics(image, box) for box in faces]
        details = [item for item in details if item is not None]
        if not details:
            return self._result("camera.jpg", 0, None, "normal", [], 0)
        metrics = details[0]
        events = self._events(metrics)
        snapshot = self.classifier.update(
            Observation(
                eyes_closed="eye_closed" in events,
                yawning="yawn" in events,
                head_down="head_down" in events,
                **metrics,
            ),
            time.monotonic(),
        )
        return self._result("camera.jpg", len(details), metrics, snapshot.level, events, snapshot.score)

    @staticmethod
    def _decode(content: bytes) -> np.ndarray:
        image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解码图片")
        return image

    def _detect_faces(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
        height, width = image.shape[:2]
        scale = min(640 / width, 640 / height)
        resized = cv2.resize(image, (round(width * scale), round(height * scale)))
        canvas = np.full((640, 640, 3), 114, dtype=np.uint8)
        pad_x = (640 - resized.shape[1]) // 2
        pad_y = (640 - resized.shape[0]) // 2
        canvas[pad_y:pad_y + resized.shape[0], pad_x:pad_x + resized.shape[1]] = resized
        tensor = canvas[:, :, ::-1].transpose(2, 0, 1).astype(np.float32)[None] / 255.0
        predictions = self.face_session.run(None, {self.face_session.get_inputs()[0].name: tensor})[0][0].T
        candidates = predictions[predictions[:, 4] >= 0.35]
        if not len(candidates):
            return []
        boxes = []
        scores = []
        for x, y, w, h, confidence in candidates[:, :5]:
            boxes.append([float(x - w / 2), float(y - h / 2), float(w), float(h)])
            scores.append(float(confidence))
        indices = cv2.dnn.NMSBoxes(boxes, scores, 0.35, 0.45)
        results = []
        for index in np.array(indices).reshape(-1):
            x, y, w, h = boxes[int(index)]
            x1 = max(0, round((x - pad_x) / scale))
            y1 = max(0, round((y - pad_y) / scale))
            x2 = min(width, round((x + w - pad_x) / scale))
            y2 = min(height, round((y + h - pad_y) / scale))
            if x2 > x1 and y2 > y1:
                results.append((x1, y1, x2, y2))
        return results

    def _landmark_metrics(self, image: np.ndarray, box: tuple[int, int, int, int]) -> dict | None:
        x1, y1, x2, y2 = box
        width, height = x2 - x1, y2 - y1
        x1, y1 = max(0, round(x1 - width * 0.1)), max(0, round(y1 - height * 0.1))
        x2, y2 = min(image.shape[1], round(x2 + width * 0.1)), min(image.shape[0], round(y2 + height * 0.1))
        roi = image[y1:y2, x1:x2]
        if not roi.size:
            return None
        face = cv2.resize(roi, (112, 112))[:, :, ::-1].transpose(2, 0, 1).astype(np.float32)[None] / 255.0
        pose, landmarks = self.pfld_session.run(None, {self.pfld_session.get_inputs()[0].name: face})
        points = landmarks[0].reshape(98, 2)
        return {
            "ear": float(self._ear(points)),
            "mar": float(self._mar(points)),
            "pitch": float(np.degrees(pose[0][1])),
        }

    @staticmethod
    def _ear(points: np.ndarray) -> float:
        def one_eye(eye):
            horizontal = np.linalg.norm(eye[0] - eye[4])
            vertical = np.linalg.norm(eye[1] - eye[7]) + np.linalg.norm(eye[2] - eye[6]) + np.linalg.norm(eye[3] - eye[5])
            return vertical / (3 * horizontal) if horizontal > 1e-6 else 0.0
        return (one_eye(points[60:68]) + one_eye(points[68:76])) / 2

    @staticmethod
    def _mar(points: np.ndarray) -> float:
        mouth = points[76:96]
        horizontal = np.linalg.norm(mouth[0] - mouth[6])
        vertical = np.linalg.norm(mouth[1] - mouth[12]) + np.linalg.norm(mouth[3] - mouth[10]) + np.linalg.norm(mouth[5] - mouth[8])
        return vertical / (3 * horizontal) if horizontal > 1e-6 else 0.0

    @staticmethod
    def _events(metrics: dict) -> list[str]:
        events = []
        if metrics["ear"] < 0.15:
            events.append("eye_closed")
        if metrics["mar"] > 0.4:
            events.append("yawn")
        if abs(metrics["pitch"]) > 30:
            events.append("head_down")
        return events

    @staticmethod
    def _result(filename, face_count, metrics, level, events, score):
        return {
            "filename": filename,
            "face_count": face_count,
            "level": level,
            "score": score,
            "events": events,
            "metrics": metrics or {"ear": 0.0, "mar": 0.0, "pitch": 0.0},
            "mode": "onnx",
        }
