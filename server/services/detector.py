from dataclasses import dataclass
import hashlib


@dataclass
class DemoDetector:
    """Lightweight runtime used until production model assets are configured."""

    name: str = "demo"
    device: str = "cpu"
    ready: bool = True

    def detect_image(self, content: bytes, filename: str, show_pose: bool = False) -> dict:
        digest = hashlib.sha256(content).hexdigest()
        return {
            "filename": filename,
            "level": "normal",
            "score": 10,
            "events": [],
            "metrics": {"ear": 0.31, "mar": 0.24, "pitch": 1.8, "roll": 0.0, "yaw": 0.0},
            "preview_id": digest[:12],
            "mode": "demo",
        }

    def detect_frame(
        self,
        content: bytes,
        session_id: str = "default",
        timestamp: float | None = None,
        show_pose: bool = False,
    ) -> dict:
        return self.detect_image(content, "camera.jpg", show_pose=show_pose)
