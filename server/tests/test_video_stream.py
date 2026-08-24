import io
import json

import cv2
import numpy as np

from server.app import create_app


class RecordingDetector:
    name = "test detector"
    device = "cpu"
    ready = True

    def __init__(self):
        self.calls = []

    def detect_frame(self, content, session_id="default", timestamp=None):
        self.calls.append((session_id, timestamp))
        return {
            "filename": "frame.jpg",
            "level": "mild",
            "score": 42,
            "events": ["eye_closed"],
            "metrics": {"ear": 0.14, "mar": 0.22, "pitch": 3.0},
            "processed_image": "data:image/jpeg;base64,ZmFrZQ==",
        }


def write_video(path, frame_count=3, fps=5):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (64, 48))
    for index in range(frame_count):
        writer.write(np.full((48, 64, 3), 30 + index * 40, dtype=np.uint8))
    writer.release()


def parse_sse(response):
    events = []
    current = {}
    for line in response.get_data(as_text=True).splitlines():
        if not line:
            if current:
                current["data"] = json.loads(current["data"])
                events.append(current)
                current = {}
            continue
        key, value = line.split(":", 1)
        current[key] = value.lstrip()
    return events


def test_video_stream_processes_every_frame_in_order_and_persists_summary(tmp_path):
    source = tmp_path / "three-frames.avi"
    write_video(source)
    detector = RecordingDetector()
    app = create_app({"TESTING": True, "DATA_DIR": tmp_path / "data"}, detector=detector)
    client = app.test_client()

    upload = client.post(
        "/api/detect/video",
        data={"file": (io.BytesIO(source.read_bytes()), "trip.avi")},
        content_type="multipart/form-data",
    )

    assert upload.status_code == 202
    job = upload.get_json()
    assert job["status"] == "ready"
    response = client.get(job["stream_url"])
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"

    events = parse_sse(response)
    frames = [event["data"] for event in events if event["event"] == "frame"]
    completed = [event["data"] for event in events if event["event"] == "complete"]
    assert [frame["frame_index"] for frame in frames] == [1, 2, 3]
    assert [frame["total_frames"] for frame in frames] == [3, 3, 3]
    assert [round(frame["media_time"], 1) for frame in frames] == [0.0, 0.2, 0.4]
    assert all(frame["processed_image"].startswith("data:image/jpeg;base64,") for frame in frames)
    assert len(completed) == 1
    assert completed[0]["processed_frames"] == 3
    assert completed[0]["record"]["source_type"] == "video"
    assert [round(call[1], 1) for call in detector.calls] == [0.0, 0.2, 0.4]
    assert len({call[0] for call in detector.calls}) == 1

    detail = client.get(f"/api/records/{completed[0]['record']['id']}").get_json()["record"]
    assert detail["details"]["processed_frames"] == 3
    assert detail["details"]["event_counts"] == {"eye_closed": 3, "yawn": 0, "head_down": 0}


def test_video_job_can_be_cancelled_before_streaming(tmp_path):
    source = tmp_path / "cancel.avi"
    write_video(source, frame_count=2)
    app = create_app({"TESTING": True, "DATA_DIR": tmp_path / "data"}, detector=RecordingDetector())
    client = app.test_client()
    job = client.post(
        "/api/detect/video",
        data={"file": (io.BytesIO(source.read_bytes()), "cancel.avi")},
        content_type="multipart/form-data",
    ).get_json()

    response = client.delete(f"/api/detect/video/{job['job_id']}")

    assert response.status_code == 200
    assert response.get_json()["status"] == "cancelled"
    stream = client.get(job["stream_url"])
    assert stream.status_code == 404
