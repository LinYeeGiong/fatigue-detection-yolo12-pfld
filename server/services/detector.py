from dataclasses import dataclass
import hashlib


@dataclass
class DemoDetector:
    """Lightweight runtime used until production model assets are configured."""

    name: str = "demo"
    device: str = "cpu"
    ready: bool = True

    def detect_image(self, content: bytes, filename: str) -> dict:
        digest = hashlib.sha256(content).hexdigest()
        return {
            "filename": filename,
            "level": "normal",
            "score": 10,
            "events": [],
            "metrics": {"ear": 0.31, "mar": 0.24, "pitch": 1.8},
            "preview_id": digest[:12],
            "mode": "demo",
        }

    def detect_frame(self, content: bytes) -> dict:
        return self.detect_image(content, "camera.jpg")
