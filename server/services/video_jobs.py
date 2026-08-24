import base64
import math
import threading
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import cv2


LEVEL_RANK = {"normal": 0, "mild": 1, "moderate": 2, "severe": 3}
EVENT_NAMES = ("eye_closed", "yawn", "head_down")


class VideoJobManager:
    def __init__(self, data_dir: Path, detector, record_store):
        self.upload_dir = Path(data_dir) / "video-jobs"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.detector = detector
        self.record_store = record_store
        self._jobs = {}
        self._lock = threading.Lock()

    def create(self, uploaded_file, filename: str) -> dict:
        job_id = uuid.uuid4().hex
        suffix = Path(filename).suffix.lower()
        path = self.upload_dir / f"{job_id}{suffix}"
        uploaded_file.save(path)
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            path.unlink(missing_ok=True)
            raise ValueError("无法读取视频文件")
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 25.0)
        total_frames = max(0, int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0))
        width = max(0, int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0))
        height = max(0, int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0))
        capture.release()
        job = {
            "job_id": job_id,
            "filename": filename,
            "path": path,
            "fps": fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "cancelled": False,
            "consumed": False,
        }
        with self._lock:
            self._jobs[job_id] = job
        return {
            "job_id": job_id,
            "status": "ready",
            "filename": filename,
            "fps": round(fps, 3),
            "total_frames": total_frames,
            "width": width,
            "height": height,
        }

    def stream(self, job_id: str) -> Iterator[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job["consumed"]:
                raise RuntimeError("视频任务已在处理或已经结束")
            job["consumed"] = True

        capture = cv2.VideoCapture(str(job["path"]))
        started = time.perf_counter()
        processed = 0
        latencies = []
        event_counts = {name: 0 for name in EVENT_NAMES}
        level_distribution = {name: 0 for name in LEVEL_RANK}
        levels = []
        scores = []
        timeline = []
        timeline_stride = max(1, math.ceil(max(job["total_frames"], 1) / 600))
        try:
            while not job["cancelled"]:
                ok, frame = capture.read()
                if not ok:
                    break
                source_index = processed
                encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 88])
                if not encoded:
                    continue
                frame_started = time.perf_counter()
                result = self.detector.detect_frame(
                    buffer.tobytes(),
                    session_id=f"video-{job_id}",
                    timestamp=source_index / job["fps"],
                )
                latency_ms = (time.perf_counter() - frame_started) * 1000
                processed += 1
                latencies.append(latency_ms)
                level = result.get("level", "normal")
                levels.append(level)
                scores.append(int(result.get("score", 0)))
                level_distribution[level] = level_distribution.get(level, 0) + 1
                for event in result.get("events", []):
                    if event in event_counts:
                        event_counts[event] += 1
                metrics = result.get("metrics") or {"ear": 0.0, "mar": 0.0, "pitch": 0.0}
                timeline_item = {
                    "frame_index": processed,
                    "media_time": round(source_index / job["fps"], 3),
                    "level": level,
                    "ear": round(float(metrics.get("ear", 0.0)), 4),
                    "mar": round(float(metrics.get("mar", 0.0)), 4),
                    "pitch": round(float(metrics.get("pitch", 0.0)), 3),
                    "latency_ms": round(latency_ms, 2),
                }
                if source_index % timeline_stride == 0:
                    timeline.append(timeline_item)
                elapsed = max(time.perf_counter() - started, 1e-6)
                processed_image = result.get("processed_image")
                if not processed_image:
                    processed_image = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("ascii")
                yield {
                    "event": "frame",
                    "data": {
                        **timeline_item,
                        "total_frames": job["total_frames"],
                        "progress": round(processed / job["total_frames"] * 100, 1) if job["total_frames"] else None,
                        "processing_fps": round(processed / elapsed, 2),
                        "events": result.get("events", []),
                        "score": int(result.get("score", 0)),
                        "metrics": metrics,
                        "processed_image": processed_image,
                    },
                }

            if job["cancelled"]:
                yield {"event": "cancelled", "data": {"job_id": job_id, "processed_frames": processed}}
                return
            if not processed:
                raise ValueError("视频中没有可分析的画面")
            elapsed = max(time.perf_counter() - started, 1e-6)
            if timeline and timeline[-1]["frame_index"] != processed:
                timeline.append(timeline_item)
            highest_level = max(levels, key=lambda item: LEVEL_RANK.get(item, 0))
            summary = {
                "status": "completed",
                "level": highest_level,
                "score": max(scores),
                "events": [name for name in EVENT_NAMES if event_counts[name]],
                "processed_frames": processed,
                "total_frames": job["total_frames"] or processed,
                "duration_seconds": round(processed / job["fps"], 2),
                "elapsed_seconds": round(elapsed, 2),
                "average_latency_ms": round(sum(latencies) / len(latencies), 2),
                "average_fps": round(processed / elapsed, 2),
                "warning_count": level_distribution.get("severe", 0),
                "event_counts": event_counts,
                "level_distribution": level_distribution,
                "timeline": timeline,
                "video": {"fps": round(job["fps"], 3), "width": job["width"], "height": job["height"]},
            }
            record = self.record_store.add("video", job["filename"], summary)
            yield {"event": "complete", "data": {**summary, "record": record}}
        except Exception as error:
            yield {"event": "error", "data": {"message": str(error) or "视频处理失败"}}
        finally:
            capture.release()
            self._remove(job_id)

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            job["cancelled"] = True
            if job["consumed"]:
                return True
        self._remove(job_id)
        return True

    def exists(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._jobs

    def _remove(self, job_id: str):
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job:
            Path(job["path"]).unlink(missing_ok=True)
