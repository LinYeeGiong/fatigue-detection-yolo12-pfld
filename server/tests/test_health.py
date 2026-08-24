from server.app import build_detector, create_app


class ReadyDetector:
    name = "test-detector"
    device = "cpu"
    ready = True


def test_health_reports_detector_and_runtime(tmp_path):
    app = create_app(
        {"TESTING": True, "DATA_DIR": tmp_path, "SECRET_KEY": "test"},
        detector=ReadyDetector(),
    )

    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ready",
        "detector": "test-detector",
        "device": "cpu",
    }


def test_missing_models_fall_back_to_explicit_demo_mode(tmp_path):
    detector = build_detector(tmp_path / "missing", "auto")
    assert detector.name == "demo"
    assert detector.device == "cpu"
