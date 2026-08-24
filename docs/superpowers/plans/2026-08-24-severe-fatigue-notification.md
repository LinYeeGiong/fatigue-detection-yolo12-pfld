# Severe Fatigue Notification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace blocking fatigue acknowledgement with a deduplicated, auto-dismissing upper-right notification.

**Architecture:** A small framework-free notification controller owns per-source severe-state transitions and dismissal timing. The existing detection workflow reports image, video, and camera risk levels to this controller; HTML and CSS provide the accessible non-modal surface.

**Tech Stack:** Vanilla JavaScript, Node test runner, Flask/Jinja, CSS.

## Global Constraints

- Detection and frame rendering must never pause for acknowledgement.
- Continuous severe frames from one source produce one notification.
- Notification timeout is 8000 ms and does not move focus.
- No new runtime dependency is introduced.

---

### Task 1: Notification Controller

**Files:**
- Create: `server/static/js/severe-notification.js`
- Create: `desktop/test/severe-notification.test.js`

**Interfaces:**
- Produces: `createSevereNotifier({ element, timeoutMs, schedule, cancelSchedule })`
- Produces: `notifier.update(source, level)`, `notifier.dismiss()`, and `notifier.reset(source)`

- [ ] Write Node tests for first severe entry, continuous-frame deduplication, non-severe re-arming, timeout, and manual dismissal.
- [ ] Run `npm test -- --test-name-pattern severe` and confirm the missing module failure.
- [ ] Implement the controller with one timer and per-source state.
- [ ] Run `npm test` and confirm all desktop tests pass.

### Task 2: Detection UI Integration

**Files:**
- Modify: `server/templates/detect.html`
- Modify: `server/static/js/detection.js`
- Modify: `server/static/css/app.css`
- Modify: `server/tests/test_pages.py`

**Interfaces:**
- Consumes: global `createSevereNotifier`
- Detection sources: `images`, `video`, and `camera`

- [ ] Change the page test to require `role="alert"`, a close control, and no `role="alertdialog"`.
- [ ] Run the focused Flask page test and confirm it fails against the modal markup.
- [ ] Add the non-modal notification markup and load the controller before `detection.js`.
- [ ] Replace `showAlert()` calls with source-level notifier updates and reset source state for new or stopped sessions.
- [ ] Replace modal CSS with upper-right notification layout, enter/exit animation, responsive placement, and reduced-motion handling.
- [ ] Run all Python and Node tests.
- [ ] Restart the local server and inspect the detection page at desktop size.

### Task 3: Optional Pose And Landmark Overlay

**Files:**
- Modify: `server/services/onnx_detector.py`
- Modify: `server/routes/detection.py`
- Modify: `server/services/video_jobs.py`
- Modify: `server/templates/detect.html`
- Modify: `server/static/js/detection.js`
- Modify: `server/static/css/app.css`
- Test: `server/tests/test_onnx_detector.py`
- Test: `server/tests/test_detection_api.py`
- Test: `server/tests/test_pages.py`

**Interfaces:**
- `detect_image(content, filename, show_pose=False)`
- `detect_frame(content, session_id="default", timestamp=None, show_pose=False)`
- Request field: `show_pose`, represented as JSON boolean or multipart string `true`

- [ ] Add failing tests for Yaw/Pitch/Roll extraction, absolute 98-point coordinates, request propagation, and the accessible toggle.
- [ ] Extend PFLD metric extraction and keep landmarks out of public stored metrics.
- [ ] Draw landmark points and pose text only when `show_pose` is true.
- [ ] Pass the option through image, video, and camera request paths.
- [ ] Add the global `显示位姿` toggle and show Roll/Yaw in result metrics.
- [ ] Run model, API, page, and full regression tests.
