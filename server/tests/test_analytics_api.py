from server.app import create_app


class Detector:
    name = "test detector"
    device = "cpu"
    ready = True


def seeded_client(tmp_path):
    app = create_app({"TESTING": True, "DATA_DIR": tmp_path}, detector=Detector())
    store = app.extensions["record_store"]
    store.add(
        "image",
        "normal.jpg",
        {
            "level": "normal",
            "score": 8,
            "events": [],
            "metrics": {"ear": 0.31, "mar": 0.18, "pitch": 2.0},
        },
    )
    store.add(
        "image",
        "warning.jpg",
        {
            "level": "severe",
            "score": 91,
            "events": ["eye_closed"],
            "metrics": {"ear": 0.11, "mar": 0.25, "pitch": 4.0},
        },
    )
    video = store.add(
        "video",
        "trip.avi",
        {
            "status": "completed",
            "level": "moderate",
            "score": 73,
            "events": ["eye_closed", "yawn"],
            "processed_frames": 5,
            "total_frames": 5,
            "duration_seconds": 1.0,
            "elapsed_seconds": 0.4,
            "average_fps": 12.5,
            "average_latency_ms": 80.0,
            "warning_count": 1,
            "event_counts": {"eye_closed": 3, "yawn": 2, "head_down": 0},
            "level_distribution": {"normal": 1, "mild": 1, "moderate": 2, "severe": 1},
            "timeline": [
                {"frame_index": 1, "media_time": 0.0, "level": "normal", "ear": 0.3, "mar": 0.2, "pitch": 1.0, "latency_ms": 70.0},
                {"frame_index": 5, "media_time": 0.8, "level": "severe", "ear": 0.1, "mar": 0.5, "pitch": 35.0, "latency_ms": 90.0},
            ],
        },
    )
    return app.test_client(), video


def test_analytics_summary_aggregates_real_records(tmp_path):
    client, _ = seeded_client(tmp_path)

    response = client.get("/api/analytics/summary")

    assert response.status_code == 200
    data = response.get_json()
    assert data["totals"] == {
        "total_tasks": 3,
        "fatigue_tasks": 2,
        "fatigue_rate": 66.7,
        "average_fps": 12.5,
        "average_latency_ms": 80.0,
    }
    assert data["risk_distribution"] == {"normal": 1, "mild": 0, "moderate": 1, "severe": 1}
    assert data["event_distribution"] == {"eye_closed": 4, "yawn": 2, "head_down": 0}
    assert data["source_distribution"] == {"image": 2, "video": 1, "camera": 0}
    assert len(data["daily_trend"]) == 1
    assert data["daily_trend"][0]["tasks"] == 3
    assert data["daily_trend"][0]["fatigue"] == 2
    assert len(data["metric_trend"]) == 1
    assert data["metric_trend"][0]["ear"] == 0.205
    assert [item["source_name"] for item in data["high_risk"]] == ["trip.avi", "warning.jpg"]
    assert data["video_experiments"][0]["processed_frames"] == 5
    assert data["video_experiments"][0]["warning_count"] == 1


def test_video_analysis_detail_returns_timeline(tmp_path):
    client, video = seeded_client(tmp_path)

    response = client.get(f"/api/analytics/videos/{video['id']}")

    assert response.status_code == 200
    data = response.get_json()["video"]
    assert data["source_name"] == "trip.avi"
    assert [item["frame_index"] for item in data["details"]["timeline"]] == [1, 5]


def test_csv_export_has_bom_headers_and_detection_values(tmp_path):
    client, _ = seeded_client(tmp_path)

    response = client.get("/api/analytics/export.csv")

    assert response.status_code == 200
    assert response.data.startswith(b"\xef\xbb\xbf")
    text = response.data.decode("utf-8-sig")
    assert "记录编号,检测时间,输入来源,文件名称,疲劳等级,风险分值" in text
    assert "trip.avi,中度,73" in text
    assert response.headers["Content-Disposition"].startswith("attachment;")
