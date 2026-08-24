from dataclasses import dataclass


@dataclass
class DemoDetector:
    """Lightweight runtime used until production model assets are configured."""

    name: str = "demo"
    device: str = "cpu"
    ready: bool = True
