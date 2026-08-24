# Streaming Video, Analytics, and UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Process and display every uploaded video frame in real time, add evidence-based analytics and exports, and deliver a polished model-agnostic desktop interface.

**Architecture:** A video-job service owns uploads, sequential OpenCV decoding, SSE events, cancellation, cleanup, and final persistence. RecordStore supplies normalized aggregations; a separate analytics blueprint exposes JSON and CSV. Local JavaScript modules drive streaming detection and canvas charts inside the existing Flask/Electron shell.

**Tech Stack:** Python 3.11, Flask, OpenCV, SQLite, pytest, HTML/CSS/JavaScript, local Chart.js, Electron, Docker.

## Global Constraints

- Process every decodable uploaded-video frame exactly once and in source order.
- Pass `frame_index / fps` to temporal classification and isolate every video session.
- CPU operation is mandatory; CUDA remains optional.
- Do not show model, framework, demo, or training terminology in user-facing pages.
- Do not report accuracy metrics without labeled ground truth.
- All runtime assets must work offline.

---

### Task 1: Video Job Contract

**Files:**
- Create: `server/services/video_jobs.py`
- Modify: `server/routes/detection.py`
- Modify: `server/services/onnx_detector.py`
- Test: `server/tests/test_video_stream.py`

**Interfaces:**
- Produces: `VideoJobManager.create(file, filename) -> dict`, `stream(job_id) -> Iterator[dict]`, and `cancel(job_id) -> bool`.
- SSE events: `frame`, `complete`, and `error`, each containing JSON data.

- [ ] Write tests with a three-frame AVI and a recording detector; assert upload returns a job ID, the stream emits frame indices `[1, 2, 3]`, detector timestamps `[0.0, 0.2, 0.4]`, and one completion event.
- [ ] Run `pytest server/tests/test_video_stream.py -v` and confirm failure because job endpoints do not exist.
- [ ] Implement job creation, sequential decode, annotated frame results, statistics, SSE serialization, cancellation, and guaranteed file/capture cleanup.
- [ ] Ensure both production and fake detectors return `processed_image` from `detect_frame`.
- [ ] Run the focused test and all detection tests until green.
- [ ] Commit as `feat: stream every video frame`.

### Task 2: Persistent Analysis Data

**Files:**
- Modify: `server/services/storage.py`
- Create: `server/routes/analytics.py`
- Modify: `server/app.py`
- Test: `server/tests/test_analytics_api.py`

**Interfaces:**
- Produces: `RecordStore.analytics(days=30) -> dict` and `RecordStore.export_rows() -> list[dict]`.
- Endpoints: `GET /api/analytics/summary`, `GET /api/analytics/videos/<id>`, and `GET /api/analytics/export.csv`.

- [ ] Write failing tests with literal records for risk, source, event, daily, performance, metric, and high-risk results plus UTF-8 CSV headers.
- [ ] Run focused tests and verify missing-route/behavior failures.
- [ ] Add backward-compatible aggregation of record JSON and video timeline retrieval.
- [ ] Implement analytics JSON and streaming CSV responses with UTF-8 BOM.
- [ ] Run storage, analytics, and full Python tests.
- [ ] Commit as `feat: add detection analytics and exports`.

### Task 3: Streaming Detection Interface

**Files:**
- Modify: `server/templates/detect.html`
- Refactor: `server/static/js/app.js`
- Create: `server/static/js/detection.js`
- Test: `server/tests/test_pages.py`

**Interfaces:**
- Consumes video job and SSE contracts from Task 1.
- Produces continuous annotated `<img>` output, progress, current metrics, timeline, cancel action, and final summary.

- [ ] Add failing page-contract tests for processed video/camera image stages, progress element, cancel control, and no sampled-frame copy.
- [ ] Run tests and confirm the new controls are absent.
- [ ] Implement upload then `EventSource`, frame replacement, metrics, progress, alerts, cancellation, and reconnect-safe cleanup.
- [ ] Serialize camera requests and display each returned annotated frame.
- [ ] Run page and API tests.
- [ ] Commit as `feat: add live annotated detection workspace`.

### Task 4: Analysis Center And Exports

**Files:**
- Create: `server/templates/analytics.html`
- Create: `server/static/js/analytics.js`
- Vendor: `server/static/vendor/chart.umd.min.js`
- Modify: `server/app.py`
- Modify: `server/templates/base.html`
- Test: `server/tests/test_pages.py`

**Interfaces:**
- Consumes `/api/analytics/summary` and video detail endpoints.
- Produces accessible labeled charts, CSV download, PNG chart download, and print/PDF report action.

- [ ] Add failing tests for `/analytics`, chart canvases, export links, and print controls.
- [ ] Run tests and verify failure.
- [ ] Add the page route, local chart runtime, summary/detail rendering, empty/error states, PNG export, and `window.print()` report flow.
- [ ] Run focused and full Python tests.
- [ ] Commit as `feat: add analysis center and report exports`.

### Task 5: Product-Wide Visual Redesign

**Files:**
- Modify: `server/templates/base.html`
- Modify: `server/templates/dashboard.html`
- Modify: `server/templates/detect.html`
- Modify: `server/templates/history.html`
- Rewrite: `server/static/css/app.css`
- Modify: `server/static/js/app.js`
- Test: `server/tests/test_pages.py`

**Interfaces:**
- Produces the Overview, Detection Center, Analysis Center, and History navigation and responsive operational layout.

- [ ] Add failing tests asserting user pages exclude `YOLO`, `PFLD`, and `demo`, and overview includes real summary containers.
- [ ] Run tests and confirm forbidden text/current structure fails.
- [ ] Replace user-facing copy, add local Lucide-style icon sprites, redesign navigation, metrics, tools, tables, states, and print styles with stable responsive dimensions.
- [ ] Check 375x812, 1280x800, and 1440x900 layouts; correct overflow, contrast, focus, and text fit.
- [ ] Run all Python and Node tests.
- [ ] Commit as `feat: redesign fatigue monitoring workspace`.

### Task 6: Delivery Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/交付说明.md`
- Modify: `docs/演示清单.md`

**Interfaces:**
- Produces rebuilt installer and verified Docker/desktop delivery instructions.

- [ ] Update Chinese documentation for every-frame playback, analytics definitions, CSV/PNG/PDF exports, CPU/GPU behavior, and evidence boundaries.
- [ ] Run `pytest server/tests -v` and `npm test` from `desktop/`.
- [ ] Build and health-check the Docker CPU image.
- [ ] Build the Windows NSIS installer and launch it or the unpacked application for desktop checks.
- [ ] Verify video frame motion and chart rendering visually at desktop and narrow viewport sizes, then confirm normal close leaves no backend process.
- [ ] Run a final diff/content scan for forbidden user-facing model terms and placeholders.
- [ ] Commit as `docs: update delivery and verification guide`.
