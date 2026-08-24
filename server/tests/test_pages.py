from server.app import create_app


class Detector:
    name = "YOLO11-face + PFLD"
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


def test_detection_workspace_has_accessible_controls_and_alert(tmp_path):
    response = make_client(tmp_path).get("/detect")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="image-files"' in html
    assert 'multiple' in html
    assert 'id="video-file"' in html
    assert 'id="camera-start"' in html
    assert 'role="alertdialog"' in html


def test_history_page_has_real_empty_state_container(tmp_path):
    response = make_client(tmp_path).get("/history")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="history-body"' in html
    assert "暂无检测记录" in html
