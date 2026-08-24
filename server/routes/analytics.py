import csv
import io

from flask import Blueprint, Response, current_app, jsonify, request


bp = Blueprint("analytics_api", __name__, url_prefix="/api/analytics")
SOURCE_LABELS = {"image": "图片", "video": "视频", "camera": "摄像头"}
LEVEL_LABELS = {"normal": "正常", "mild": "轻度", "moderate": "中度", "severe": "重度"}


@bp.get("/summary")
def summary():
    days = request.args.get("days", default=30, type=int)
    return jsonify(current_app.extensions["record_store"].analytics(days=days or 30))


@bp.get("/videos/<int:record_id>")
def video_detail(record_id: int):
    record = current_app.extensions["record_store"].get(record_id)
    if record is None or record["source_type"] != "video":
        return jsonify(error="视频分析记录不存在"), 404
    return jsonify(video=record)


@bp.get("/export.csv")
def export_csv():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        ["记录编号", "检测时间", "输入来源", "文件名称", "疲劳等级", "风险分值", "行为事件", "处理帧数", "平均帧率", "平均延迟(ms)"]
    )
    for record in current_app.extensions["record_store"].export_rows():
        details = record["details"]
        events = details.get("events", [])
        writer.writerow(
            [
                record["id"],
                record["created_at"],
                SOURCE_LABELS.get(record["source_type"], record["source_type"]),
                record["source_name"],
                LEVEL_LABELS.get(record["level"], record["level"]),
                record["score"],
                "/".join(events),
                details.get("processed_frames", ""),
                details.get("average_fps", ""),
                details.get("average_latency_ms", ""),
            ]
        )
    body = "\ufeff" + output.getvalue()
    return Response(
        body,
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=detection-analysis.csv"},
    )
