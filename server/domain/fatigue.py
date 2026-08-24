from collections import deque
from dataclasses import dataclass, field
from typing import Deque


LEVEL_RANK = {"normal": 0, "mild": 1, "moderate": 2, "severe": 3}


@dataclass(frozen=True)
class Observation:
    eyes_closed: bool = False
    yawning: bool = False
    head_down: bool = False
    ear: float | None = None
    mar: float | None = None
    pitch: float | None = None


@dataclass(frozen=True)
class FatigueSnapshot:
    level: str
    score: int
    active_events: tuple[str, ...]
    counts: dict[str, int] = field(default_factory=dict)


class FatigueClassifier:
    labels = {
        "normal": "正常",
        "mild": "轻度疲劳",
        "moderate": "中度疲劳",
        "severe": "重度疲劳",
    }

    def __init__(self, window_seconds: float = 60.0):
        self.window_seconds = window_seconds
        self._events: dict[str, Deque[float]] = {
            "eye_closed": deque(),
            "yawn": deque(),
            "head_down": deque(),
        }
        self._started: dict[str, float | None] = {key: None for key in self._events}
        self._previous = Observation()

    def update(self, observation: Observation, timestamp: float) -> FatigueSnapshot:
        flags = {
            "eye_closed": observation.eyes_closed,
            "yawn": observation.yawning,
            "head_down": observation.head_down,
        }
        previous_flags = {
            "eye_closed": self._previous.eyes_closed,
            "yawn": self._previous.yawning,
            "head_down": self._previous.head_down,
        }

        for event, active in flags.items():
            if active and not previous_flags[event]:
                self._events[event].append(timestamp)
                self._started[event] = timestamp
            elif not active:
                self._started[event] = None
            cutoff = timestamp - self.window_seconds
            while self._events[event] and self._events[event][0] < cutoff:
                self._events[event].popleft()

        candidates = ["normal"]
        eye_duration = self._duration("eye_closed", timestamp)
        head_duration = self._duration("head_down", timestamp)
        if eye_duration >= 4 or head_duration >= 6 or len(self._events["yawn"]) >= 4:
            candidates.append("severe")
        elif eye_duration >= 3 or head_duration >= 4:
            candidates.append("moderate")
        elif eye_duration >= 2 or head_duration >= 2 or len(self._events["yawn"]) >= 3:
            candidates.append("mild")

        level = max(candidates, key=LEVEL_RANK.__getitem__)
        score = {"normal": 10, "mild": 45, "moderate": 70, "severe": 95}[level]
        self._previous = observation
        return FatigueSnapshot(
            level=level,
            score=score,
            active_events=tuple(event for event, active in flags.items() if active),
            counts={event: len(events) for event, events in self._events.items()},
        )

    def _duration(self, event: str, timestamp: float) -> float:
        started = self._started[event]
        return 0.0 if started is None else max(0.0, timestamp - started)
