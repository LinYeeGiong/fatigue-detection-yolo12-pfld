from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


class RecordStore:
    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / "fatigue.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    level TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add(self, source_type: str, source_name: str, result: dict) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO records (source_type, source_name, level, score, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (source_type, source_name, result["level"], result["score"], json.dumps(result, ensure_ascii=False), created_at),
            )
            record_id = cursor.lastrowid
        return {"id": record_id, "source_type": source_type, "source_name": source_name, "level": result["level"], "score": result["score"], "created_at": created_at}

    def list(self, limit: int = 100) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, source_type, source_name, level, score, created_at FROM records ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, record_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["details"] = json.loads(record["details"])
        return record

    def analytics(self, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 3650)))
        records = [record for record in self._all() if self._parse_date(record["created_at"]) >= cutoff]
        risk = {name: 0 for name in ("normal", "mild", "moderate", "severe")}
        sources = {name: 0 for name in ("image", "video", "camera")}
        events = {name: 0 for name in ("eye_closed", "yawn", "head_down")}
        daily = defaultdict(lambda: {"tasks": 0, "fatigue": 0, "metrics": []})
        performance = []
        video_experiments = []
        high_risk = []

        for record in records:
            details = record["details"]
            level = record["level"]
            risk[level] = risk.get(level, 0) + 1
            sources[record["source_type"]] = sources.get(record["source_type"], 0) + 1
            date = self._parse_date(record["created_at"]).date().isoformat()
            daily[date]["tasks"] += 1
            if level != "normal":
                daily[date]["fatigue"] += 1
            if level in {"moderate", "severe"}:
                high_risk.append(self._public_record(record))

            event_counts = details.get("event_counts")
            if isinstance(event_counts, dict):
                for name in events:
                    events[name] += int(event_counts.get(name, 0))
            else:
                for name in details.get("events", []):
                    if name in events:
                        events[name] += 1

            metrics = details.get("metrics")
            if isinstance(metrics, dict):
                daily[date]["metrics"].append(metrics)
            for point in details.get("timeline", []):
                if isinstance(point, dict):
                    daily[date]["metrics"].append(point)

            if record["source_type"] == "video":
                if details.get("average_fps") is not None and details.get("average_latency_ms") is not None:
                    performance.append((float(details["average_fps"]), float(details["average_latency_ms"])))
                video_experiments.append(
                    {
                        **self._public_record(record),
                        "processed_frames": int(details.get("processed_frames", 0)),
                        "total_frames": int(details.get("total_frames", 0)),
                        "duration_seconds": float(details.get("duration_seconds", 0)),
                        "average_fps": float(details.get("average_fps", 0)),
                        "average_latency_ms": float(details.get("average_latency_ms", 0)),
                        "warning_count": int(details.get("warning_count", 0)),
                        "event_counts": details.get("event_counts", {name: 0 for name in events}),
                        "level_distribution": details.get("level_distribution", {name: 0 for name in risk}),
                    }
                )

        total = len(records)
        fatigue = total - risk.get("normal", 0)
        average_fps = round(sum(item[0] for item in performance) / len(performance), 2) if performance else 0.0
        average_latency = round(sum(item[1] for item in performance) / len(performance), 2) if performance else 0.0
        daily_trend = []
        metric_trend = []
        for date in sorted(daily):
            bucket = daily[date]
            daily_trend.append({"date": date, "tasks": bucket["tasks"], "fatigue": bucket["fatigue"]})
            points = bucket["metrics"]
            if points:
                metric_trend.append(
                    {
                        "date": date,
                        "ear": round(sum(float(item.get("ear", 0)) for item in points) / len(points), 3),
                        "mar": round(sum(float(item.get("mar", 0)) for item in points) / len(points), 3),
                        "pitch": round(sum(float(item.get("pitch", 0)) for item in points) / len(points), 2),
                    }
                )
        return {
            "totals": {
                "total_tasks": total,
                "fatigue_tasks": fatigue,
                "fatigue_rate": round(fatigue / total * 100, 1) if total else 0.0,
                "average_fps": average_fps,
                "average_latency_ms": average_latency,
            },
            "risk_distribution": risk,
            "event_distribution": events,
            "source_distribution": sources,
            "daily_trend": daily_trend,
            "metric_trend": metric_trend,
            "high_risk": high_risk[:10],
            "video_experiments": video_experiments[:20],
        }

    def export_rows(self) -> list[dict]:
        return self._all()

    def _all(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
        records = []
        for row in rows:
            record = dict(row)
            record["details"] = json.loads(record["details"])
            records.append(record)
        return records

    @staticmethod
    def _parse_date(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _public_record(record: dict) -> dict:
        return {key: record[key] for key in ("id", "source_type", "source_name", "level", "score", "created_at")}

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection
