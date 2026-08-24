import base64
import binascii
import json

import cv2

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context, url_for
from werkzeug.utils import secure_filename


bp = Blueprint("detection_api", __name__, url_prefix="/api")
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


@bp.post("/detect/images")
def detect_images():
    files = request.files.getlist("files")
    if not files or all(not item.filename for item in files):
        return jsonify(error="请选择至少一张图片"), 400
    for item in files:
        if _extension(item.filename or "") not in IMAGE_EXTENSIONS:
            return jsonify(error=f"不支持的图片格式: {item.filename}"), 400

    detector = current_app.extensions["detector"]
    store = current_app.extensions["record_store"]
    results = []
    for item in files:
        filename = secure_filename(item.filename) or "image.jpg"
        result = detector.detect_image(item.read(), filename)
        result["record"] = store.add("image", filename, result)
        results.append(result)
    return jsonify(results=results, alert=any(item["level"] == "severe" for item in results))


@bp.post("/detect/frame")
def detect_frame():
    payload = request.get_json(silent=True) or {}
    encoded = payload.get("frame", "")
    if "," in encoded:
        encoded = encoded.split(",", 1)[1]
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return jsonify(error="视频帧编码无效"), 400
    if not content:
        return jsonify(error="视频帧不能为空"), 400
    session_id = str(payload.get("session_id") or "default")[:128]
    result = current_app.extensions["detector"].detect_frame(content, session_id=session_id)
    return jsonify(result=result, alert=result["level"] == "severe")


@bp.post("/detect/video")
def detect_video():
    item = request.files.get("file")
    if item is None or not item.filename:
        return jsonify(error="请选择视频文件"), 400
    if _extension(item.filename) not in VIDEO_EXTENSIONS:
        return jsonify(error=f"不支持的视频格式: {item.filename}"), 400
    filename = secure_filename(item.filename) or "video.mp4"
    try:
        job = current_app.extensions["video_jobs"].create(item, filename)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    job["stream_url"] = url_for("detection_api.video_events", job_id=job["job_id"])
    return jsonify(job), 202


@bp.get("/detect/video/<job_id>/events")
def video_events(job_id: str):
    manager = current_app.extensions["video_jobs"]
    if not manager.exists(job_id):
        return jsonify(error="视频任务不存在"), 404

    def generate():
        try:
            for message in manager.stream(job_id):
                payload = json.dumps(message["data"], ensure_ascii=False, separators=(",", ":"))
                yield f"event: {message['event']}\ndata: {payload}\n\n"
        except (KeyError, RuntimeError) as error:
            payload = json.dumps({"message": str(error)}, ensure_ascii=False)
            yield f"event: error\ndata: {payload}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp.delete("/detect/video/<job_id>")
def cancel_video(job_id: str):
    if not current_app.extensions["video_jobs"].cancel(job_id):
        return jsonify(error="视频任务不存在"), 404
    return jsonify(status="cancelled")


@bp.get("/records")
def records():
    return jsonify(records=current_app.extensions["record_store"].list())


@bp.get("/records/<int:record_id>")
def record_detail(record_id: int):
    record = current_app.extensions["record_store"].get(record_id)
    return (jsonify(record=record), 200) if record else (jsonify(error="记录不存在"), 404)
