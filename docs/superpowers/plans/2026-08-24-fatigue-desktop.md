# Fatigue Detection Desktop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows Electron application around a tested Flask fatigue-detection service, with CPU-first Docker deployment and concise delivery documentation.

**Architecture:** A Flask JSON/API and server-rendered dashboard provide one reusable UI for Electron and Docker. Electron supervises the local Python sidecar. Detection is behind an adapter so tests and UI run deterministically while existing YOLO12/PFLD assets remain the production integration point.

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

- [x] Write tests proving duration/frequency thresholds and CPU fallback behavior.
- [x] Run `python -m pytest server/tests -v` and confirm failures are caused by missing modules.
- [x] Implement typed observations, rolling events, configuration, health endpoint, and detector protocol.
- [x] Run the backend tests and commit `feat: add fatigue service foundation`.

### Task 2: Multi-Source Detection And Persistence

**Files:** Create `server/routes/detection.py`, `server/models.py`, `server/services/storage.py`, `server/tests/test_detection_api.py`; modify `server/app.py`.

**Interfaces:** `POST /api/detect/images`, `POST /api/detect/video`, `POST /api/detect/frame`, `GET /api/records`, and `GET /api/records/<id>` return stable JSON envelopes.

- [x] Write failing API tests for valid batches, invalid extensions, absent files, persistence, and severe alerts.
- [x] Implement bounded uploads, safe filenames, result storage, and adapter calls.
- [x] Run all server tests and commit `feat: add multi-source detection APIs`.

### Task 3: Reused Web Experience And Visual System

**Files:** Create `server/templates/base.html`, `dashboard.html`, `detect.html`, `history.html`, `server/static/css/app.css`, `server/static/js/app.js`; add route tests.

**Interfaces:** Pages consume the Task 2 endpoints and render loading, empty, success, error, and severe-warning states.

- [x] Write failing route/content tests for navigation, device display, upload controls, camera controls, result table, and alert dialog.
- [x] Implement the dense operations UI using persisted design tokens and accessible controls.
- [x] Verify the 1380x860 packaged desktop layout with screenshot and accessibility-tree inspection, then commit `feat: build monitoring workspace`.

### Task 4: Electron Lifecycle And Windows Packaging

**Files:** Create `desktop/package.json`, `desktop/src/main.js`, `desktop/src/backend.js`, `desktop/src/preload.js`, `desktop/test/backend.test.js`, `scripts/build-server.ps1`, `scripts/build-windows.ps1`.

**Interfaces:** `findFreePort()`, `resolveBackendCommand()`, `waitForHealth()`, and `stopBackend()` manage the sidecar without orphan processes.

- [x] Write Node tests for port selection, command resolution, readiness timeout, and shutdown.
- [x] Implement secure BrowserWindow defaults, health-gated startup, user-data paths, and electron-builder configuration.
- [x] Run `npm test`, package an unpacked Windows app, smoke-test start/exit, and commit the Electron desktop shell.

### Task 5: Docker And Delivery Materials

**Files:** Create `Dockerfile`, `compose.yaml`, `compose.gpu.yaml`, `.dockerignore`, `.gitignore`, `README.md`, `docs/交付说明.md`, `docs/演示清单.md`.

**Interfaces:** `docker compose up --build` exposes the same app and persists `/data`; GPU override sets the runtime device preference only.

- [x] Add configuration tests for container binding and desktop localhost behavior.
- [x] Build the CPU image and verify its host health endpoint reports the ONNX detector.
- [x] Document Windows install, Docker startup, model placement, demo flow, limitations, and troubleshooting.
- [x] Run the complete backend/Node/build verification and commit the delivery package.
