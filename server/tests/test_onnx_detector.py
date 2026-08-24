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
