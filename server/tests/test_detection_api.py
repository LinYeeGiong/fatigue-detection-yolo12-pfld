import base64
import io
from pathlib import Path

import cv2
import numpy as np

from server.app import create_app


class FakeDetector:
    name = "fake"
    device = "cpu"
    ready = True

    def detect_image(self, content: bytes, filename: str) -> dict:
        level = "severe" if "closed" in filename else "normal"
        return {
            "filename": filename,
            "level": level,
            "score": 95 if level == "severe" else 10,
            "events": ["eye_closed"] if level == "severe" else [],
            "metrics": {"ear": 0.12 if level == "severe" else 0.31, "mar": 0.22, "pitch": 2.0},
        }

    def detect_frame(self, content: bytes) -> dict:
        return self.detect_image(content, "camera.jpg")


def make_client(tmp_path):
    app = create_app(
        {"TESTING": True, "DATA_DIR": tmp_path, "SECRET_KEY": "test"},
        detector=FakeDetector(),
    )
    return app.test_client()


def test_batch_image_detection_returns_each_result_and_alert(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/detect/images",
        data={
            "files": [
                (io.BytesIO(b"normal"), "normal.jpg"),
                (io.BytesIO(b"closed"), "closed_eyes.png"),
            ]
        },
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert [item["level"] for item in payload["results"]] == ["normal", "severe"]
    assert payload["alert"] is True


def test_image_detection_rejects_unsupported_extension(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/detect/images",
        data={"files": (io.BytesIO(b"x"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "不支持的图片格式: notes.txt"


def test_frame_detection_accepts_data_url(tmp_path):
    client = make_client(tmp_path)
    encoded = base64.b64encode(b"frame").decode("ascii")
    response = client.post("/api/detect/frame", json={"frame": f"data:image/jpeg;base64,{encoded}"})
    assert response.status_code == 200
    assert response.get_json()["result"]["level"] == "normal"


def test_detection_records_are_persisted(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/detect/images",
        data={"files": (io.BytesIO(b"closed"), "closed_eyes.jpg")},
        content_type="multipart/form-data",
    )
    response = client.get("/api/records")
    records = response.get_json()["records"]
    assert len(records) == 1
    assert records[0]["source_type"] == "image"
    assert records[0]["level"] == "severe"


def test_video_upload_requires_supported_file(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/detect/video",
        data={"file": (io.BytesIO(b"video"), "clip.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_video_upload_analyzes_sampled_frames(tmp_path):
    path = tmp_path / "sample.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 5, (64, 48))
    for value in (20, 80, 140):
        writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
    writer.release()

    client = make_client(tmp_path / "data")
    response = client.post(
        "/api/detect/video",
        data={"file": (io.BytesIO(path.read_bytes()), "sample.avi")},
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "completed"
    assert payload["analyzed_frames"] == 3
    assert payload["record"]["source_type"] == "video"
