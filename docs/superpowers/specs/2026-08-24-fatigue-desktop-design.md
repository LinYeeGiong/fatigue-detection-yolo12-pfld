# Driver Fatigue Monitoring Desktop Design

## Goal

Deliver a Windows desktop application that detects closed eyes, yawning, and head-down behavior from images, uploaded videos, and a camera. The system uses the existing inference weights without retraining, classifies risk as normal, mild, moderate, or severe, and provides reviewable records and analysis exports.

## Product Experience

The application is an operational monitoring tool, not a model demonstration. User-facing pages must not mention model families, framework names, demo modes, or training claims. The persistent navigation contains Overview, Detection Center, Analysis Center, and History. The visual system uses a light neutral workspace, a dark compact sidebar, blue primary actions, and green, amber, orange, and red semantic risk colors. Layouts target 1280x800 and 1440x900 while remaining usable at 375px. Focus states, non-color chart labels, loading states, empty states, errors, and reduced-motion behavior are required.

## Detection Workflows

- Batch images are uploaded together and return an annotated result, fatigue level, risk score, events, and EAR/MAR/Pitch values for each image.
- Uploaded video creates a processing job. A server-sent events endpoint reads every decodable frame in order, performs inference with a unique temporal session and the frame's media timestamp, and emits the annotated JPEG, frame number, total frames, progress, media time, level, events, metrics, latency, and effective processing FPS. The browser continuously replaces the displayed processed frame. No sampling interval or analyzed-frame cap is allowed.
- Camera monitoring retains the local preview used for capture but presents the annotated server result as the primary visible output. Requests are serialized to avoid overlapping inference.
- Severe results open a clear safety warning. Disconnect or cancellation closes the video capture and removes temporary uploads.

## Persistence And Analytics

Each completed image or video task is stored in SQLite. Video details include duration, total and processed frames, elapsed processing time, average latency/FPS, event counts, warning count, level distribution, and a downsampled metric timeline suitable for charts. Existing databases remain readable.

The Analysis Center shows total tasks, fatigue rate, average throughput and latency, risk distribution, behavior-event distribution, input-source distribution, daily task trend, metric trend, recent high-risk records, and per-video experiment details. It must distinguish measured throughput from model accuracy: without labeled ground truth the UI does not show mAP, precision, recall, or warning accuracy.

Exports include filtered record data as UTF-8 BOM CSV, analysis chart canvases as PNG, and a print-optimized report that Electron or the browser can save as PDF. Exported values come from persisted detections only.

## Architecture

`server/services/video_jobs.py` owns temporary video jobs and SSE frame generation. `server/services/storage.py` owns records and aggregation queries. `server/routes/detection.py` owns detection and job endpoints, while a focused analytics blueprint owns summary and CSV endpoints. The plain JavaScript frontend separates shared shell behavior, detection streaming, chart rendering, and history rendering where practical. Charts use a locally bundled library so Electron and Docker require no internet access.

Electron starts the packaged Python service on localhost and stores writable data in its user-data directory. CPU is the acceptance baseline; an available CUDA provider may be used automatically. Docker Compose remains an additional CPU-first deployment option.

## Error Handling And Verification

Invalid uploads return Chinese 4xx messages. SSE emits a structured error event before cleanup when decoding or inference fails. Jobs reject duplicate consumers and expose cancellation. Automated tests prove every source frame is processed once and in order, media timestamps are preserved, completion records contain analysis data, aggregations and CSV are correct, and pages contain the required controls without forbidden implementation labels. Browser and Electron checks cover live frame replacement, charts, exports, warnings, responsive layout, and application shutdown.

## Deliverables

Delivery includes source code, Windows installer, CPU Docker configuration with optional GPU override, a concise Chinese usage/acceptance guide, and demonstration material. It makes no claim of retraining or unsupported accuracy improvement.
