from pathlib import Path

import pytest

from server.services.onnx_detector import OnnxDetector


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT_ROOT.parent / "【硕士论文】疲劳驾驶检测（YOLO改进+PFLD）" / "PFPLD" / "close_eyes.jpg"


@pytest.mark.skipif(not (PROJECT_ROOT / "models" / "yolo11_face.onnx").exists(), reason="model assets not staged")
def test_existing_onnx_models_detect_face_and_landmark_metrics():
    detector = OnnxDetector(PROJECT_ROOT / "models")

    result = detector.detect_image(SAMPLE.read_bytes(), SAMPLE.name)

    assert detector.ready is True
    assert detector.name == "YOLO11-face + PFLD (ONNX)"
    assert result["face_count"] >= 1
    assert 0 <= result["metrics"]["ear"] <= 1
    assert 0 <= result["metrics"]["mar"] <= 2
    assert -180 <= result["metrics"]["pitch"] <= 180
    assert result["mode"] == "onnx"
    assert result["processed_image"].startswith("data:image/jpeg;base64,")


def test_frame_state_is_isolated_by_session_and_no_face_clears_active_state():
    detector = OnnxDetector.__new__(OnnxDetector)
    detector._decode = lambda content: object()
    detector._detect_faces = lambda image: [(0, 0, 10, 10)] if image is not None else []
    detector._landmark_metrics = lambda image, box: {"ear": 0.1, "mar": 0.2, "pitch": 0.0}

    detector.detect_frame(b"x", session_id="driver-a", timestamp=0)
    severe = detector.detect_frame(b"x", session_id="driver-a", timestamp=4.1)
    fresh = detector.detect_frame(b"x", session_id="driver-b", timestamp=4.1)

    assert severe["level"] == "severe"
    assert fresh["level"] == "normal"

    detector._detect_faces = lambda image: []
    detector.detect_frame(b"x", session_id="driver-a", timestamp=5)
    detector._detect_faces = lambda image: [(0, 0, 10, 10)]
    reset = detector.detect_frame(b"x", session_id="driver-a", timestamp=8)
    assert reset["level"] == "normal"
