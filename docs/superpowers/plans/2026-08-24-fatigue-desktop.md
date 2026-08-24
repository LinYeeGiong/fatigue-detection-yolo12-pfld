# Fatigue Detection Desktop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows Electron application around a tested Flask fatigue-detection service, with CPU-first Docker deployment and concise delivery documentation.

**Architecture:** A Flask JSON/API and server-rendered dashboard provide one reusable UI for Electron and Docker. Electron supervises the local Python sidecar. Detection is behind an adapter so tests and UI run deterministically while existing YOLO11/PFLD assets remain the production integration point.

**Tech Stack:** Python 3.11, Flask, SQLAlchemy, OpenCV/ONNX Runtime adapter, pytest, Electron, Node test runner, Bootstrap-compatible HTML/CSS, Docker Compose.

## Global Constraints

- Do not retrain or claim YOLO12 model results.
- Windows CPU execution is mandatory; CUDA is optional and must fall back cleanly.
- Preserve the original repository; all work stays in `fatigue-detection-desktop/`.
- Use normal/mild/moderate/severe levels and exclude distracted-gaze claims.
- Electron and Docker reuse the same Flask pages and API.

---

### Task 1: Backend Foundation And Fatigue Rules

**Files:** Create `server/app.py`, `server/config.py`, `server/domain/fatigue.py`, `server/services/detector.py`, `server/tests/test_fatigue.py`, `server/tests/test_health.py`, `server/requirements*.txt`.

**Interfaces:** `FatigueClassifier.update(observation, timestamp) -> FatigueSnapshot`; `create_app(config=None, detector=None) -> Flask`; `GET /api/health` reports readiness and device.

- [ ] Write tests proving duration/frequency thresholds and CPU fallback behavior.
- [ ] Run `python -m pytest server/tests -v` and confirm failures are caused by missing modules.
- [ ] Implement typed observations, rolling events, configuration, health endpoint, and detector protocol.
- [ ] Run the backend tests and commit `feat: add fatigue service foundation`.

### Task 2: Multi-Source Detection And Persistence

**Files:** Create `server/routes/detection.py`, `server/models.py`, `server/services/storage.py`, `server/tests/test_detection_api.py`; modify `server/app.py`.

**Interfaces:** `POST /api/detect/images`, `POST /api/detect/video`, `POST /api/detect/frame`, `GET /api/records`, and `GET /api/records/<id>` return stable JSON envelopes.

- [ ] Write failing API tests for valid batches, invalid extensions, absent files, persistence, and severe alerts.
- [ ] Implement bounded uploads, safe filenames, result storage, and adapter calls.
- [ ] Run all server tests and commit `feat: add multi-source detection APIs`.

### Task 3: Reused Web Experience And Visual System

**Files:** Create `server/templates/base.html`, `dashboard.html`, `detect.html`, `history.html`, `server/static/css/app.css`, `server/static/js/app.js`; add route tests.

**Interfaces:** Pages consume the Task 2 endpoints and render loading, empty, success, error, and severe-warning states.

- [ ] Write failing route/content tests for navigation, device display, upload controls, camera controls, result table, and alert dialog.
- [ ] Implement the dense operations UI using persisted design tokens and accessible controls.
- [ ] Verify 1280x800 and 1440x900 layouts in a real browser, then commit `feat: build monitoring workspace`.

### Task 4: Electron Lifecycle And Windows Packaging

**Files:** Create `desktop/package.json`, `desktop/src/main.js`, `desktop/src/backend.js`, `desktop/src/preload.js`, `desktop/test/backend.test.js`, `scripts/build-server.ps1`, `scripts/build-windows.ps1`.

**Interfaces:** `findFreePort()`, `resolveBackendCommand()`, `waitForHealth()`, and `stopBackend()` manage the sidecar without orphan processes.

- [ ] Write Node tests for port selection, command resolution, readiness timeout, and shutdown.
- [ ] Implement secure BrowserWindow defaults, health-gated startup, user-data paths, and electron-builder configuration.
- [ ] Run `npm test`, package an unpacked Windows app, smoke-test start/exit, and commit `feat: add Electron desktop shell`.

### Task 5: Docker And Delivery Materials

**Files:** Create `Dockerfile`, `compose.yaml`, `compose.gpu.yaml`, `.dockerignore`, `.gitignore`, `README.md`, `docs/交付说明.md`, `docs/演示清单.md`.

**Interfaces:** `docker compose up --build` exposes the same app and persists `/data`; GPU override sets the runtime device preference only.

- [ ] Add configuration tests for container paths and production secret requirements.
- [ ] Build the CPU image, run its health check, and verify persisted records.
- [ ] Document Windows install, Docker startup, model placement, demo flow, limitations, and troubleshooting.
- [ ] Run the complete backend/Node/build verification and commit `docs: prepare delivery package`.
