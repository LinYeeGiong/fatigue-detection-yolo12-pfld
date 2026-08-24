import os
from pathlib import Path

from flask import Flask, jsonify, render_template

from server.services.detector import DemoDetector
from server.services.storage import RecordStore
from server.services.video_jobs import VideoJobManager


def build_detector(model_dir: Path, device_preference: str = "auto"):
    model_dir = Path(model_dir)
    required = (model_dir / "yolo11_face.onnx", model_dir / "pfpld.onnx")
    if not all(path.is_file() for path in required):
        return DemoDetector()
    try:
        from server.services.onnx_detector import OnnxDetector

        return OnnxDetector(model_dir, device_preference)
    except Exception:
        return DemoDetector()


def create_app(config: dict | None = None, detector=None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="development-only",
        DATA_DIR=Path(os.environ.get("FATIGUE_DATA_DIR", Path(__file__).resolve().parent.parent / "data")),
        MODEL_DIR=Path(os.environ.get("FATIGUE_MODEL_DIR", Path(__file__).resolve().parent.parent / "models")),
        DEVICE_PREFERENCE=os.environ.get("FATIGUE_DEVICE", "auto"),
        MAX_CONTENT_LENGTH=100 * 1024 * 1024,
    )
    if config:
        app.config.update(config)
    app.config["DATA_DIR"] = Path(app.config["DATA_DIR"])
    app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    app.extensions["detector"] = detector or build_detector(app.config["MODEL_DIR"], app.config["DEVICE_PREFERENCE"])
    app.extensions["record_store"] = RecordStore(app.config["DATA_DIR"])
    app.extensions["video_jobs"] = VideoJobManager(
        app.config["DATA_DIR"], app.extensions["detector"], app.extensions["record_store"]
    )

    from server.routes.detection import bp as detection_bp
    from server.routes.analytics import bp as analytics_bp

    app.register_blueprint(detection_bp)
    app.register_blueprint(analytics_bp)

    @app.get("/api/health")
    def health():
        runtime = app.extensions["detector"]
        return jsonify(
            status="ready" if runtime.ready else "starting",
            detector=runtime.name,
            device=runtime.device,
        )

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html", page="dashboard", detector=app.extensions["detector"])

    @app.get("/detect")
    def detect_page():
        return render_template("detect.html", page="detect", detector=app.extensions["detector"])

    @app.get("/history")
    def history_page():
        return render_template("history.html", page="history", detector=app.extensions["detector"])

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5001")))
