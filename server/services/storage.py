import json
import sqlite3
from datetime import datetime, timezone
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

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection
