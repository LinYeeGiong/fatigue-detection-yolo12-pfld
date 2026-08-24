from server.app import create_app


class Detector:
    name = "YOLO12-face + PFLD"
    device = "cpu"
    ready = True


def make_client(tmp_path):
    app = create_app({"TESTING": True, "DATA_DIR": tmp_path}, detector=Detector())
    return app.test_client()


def test_dashboard_exposes_status_and_primary_workflows(tmp_path):
    response = make_client(tmp_path).get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "驾驶员疲劳监测系统" in html
    assert 'data-device="cpu"' in html
    assert "批量图片" in html
    assert "视频分析" in html
    assert "实时监测" in html


def test_detection_workspace_has_accessible_controls_and_nonblocking_alert(tmp_path):
    response = make_client(tmp_path).get("/detect")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="image-files"' in html
    assert 'multiple' in html
    assert 'id="video-file"' in html
    assert 'id="camera-start"' in html
    assert 'id="video-processed"' in html
    assert 'id="video-progress"' in html
    assert 'id="video-cancel"' in html
    assert 'id="camera-processed"' in html
    assert 'id="pose-overlay-toggle"' in html
    assert 'aria-pressed="false"' in html
    assert 'id="severe-alert"' in html
    assert 'role="alert"' in html
    assert 'id="alert-close"' in html
    assert 'aria-label="关闭疲劳预警"' in html
    assert 'role="alertdialog"' not in html
    assert 'aria-modal="true"' not in html
    assert "抽帧" not in html


def test_history_page_has_real_empty_state_container(tmp_path):
    response = make_client(tmp_path).get("/history")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="history-body"' in html
    assert "暂无检测记录" in html


def test_analytics_page_has_charts_and_export_controls(tmp_path):
    response = make_client(tmp_path).get("/analytics")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="risk-chart"' in html
    assert 'id="event-chart"' in html
    assert 'id="source-chart"' in html
    assert 'id="trend-chart"' in html
    assert 'id="metric-chart"' in html
    assert 'href="/api/analytics/export.csv"' in html
    assert 'id="export-charts"' in html
    assert 'id="print-report"' in html


def test_user_pages_hide_model_and_demo_implementation_terms(tmp_path):
    client = make_client(tmp_path)
    for path in ("/", "/detect", "/analytics", "/history"):
        html = client.get(path).get_data(as_text=True).lower()
        assert "yolo" not in html
        assert "pfld" not in html
        assert "demo" not in html


def test_dashboard_uses_persisted_summary_containers(tmp_path):
    html = make_client(tmp_path).get("/").get_data(as_text=True)
    assert 'id="overview-total"' in html
    assert 'id="overview-fatigue-rate"' in html
    assert 'id="overview-risk-bars"' in html
