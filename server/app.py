from pathlib import Path

from flask import Flask, jsonify

from server.services.detector import DemoDetector


def create_app(config: dict | None = None, detector=None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="development-only",
        DATA_DIR=Path(__file__).resolve().parent.parent / "data",
    )
    if config:
        app.config.update(config)
    app.config["DATA_DIR"] = Path(app.config["DATA_DIR"])
    app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    app.extensions["detector"] = detector or DemoDetector()

    @app.get("/api/health")
    def health():
        runtime = app.extensions["detector"]
        return jsonify(
            status="ready" if runtime.ready else "starting",
            detector=runtime.name,
            device=runtime.device,
        )

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5001)
