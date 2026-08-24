# Fatigue Detection Desktop Design

## Goal

Deliver a Windows desktop fatigue-monitoring system using existing YOLO11-face and PFLD weights without retraining. Electron hosts the reused Flask web experience; the same backend can run through Docker for browser access.

## Architecture

`desktop/` owns the Electron lifecycle and starts a packaged Python sidecar on a free localhost port. `server/` owns HTTP endpoints, persistence, uploads, inference adapters, and time-based fatigue classification. The browser UI never accesses model files directly. In development, a deterministic demo detector keeps UI and automated tests runnable without loading heavyweight models; production selects the existing model adapter when compatible weights and runtime are available.

## Functional Scope

- Dashboard with runtime device, service health, recent totals, and direct detection actions.
- Batch image upload, video upload/analysis, and webcam frame analysis.
- Observable events: prolonged eye closure, yawning, and head-down posture. “Distracted gaze” is excluded.
- Levels: normal, mild, moderate, and severe, computed from duration and event frequency in a rolling time window.
- Visible severe warning, history records, result detail, and summary charts.
- CPU is the required baseline. CUDA is detected and used when available; inability to use CUDA must fall back to CPU.

## Desktop And Deployment

Electron waits for `/api/health`, opens only localhost URLs, terminates the sidecar on exit, and stores writable data under the user-data directory. Windows packaging includes the Electron shell and a PyInstaller-built server. Docker Compose provides a CPU image; an optional GPU override is documented but not required for acceptance.

## Visual Direction

Use a quiet operations-dashboard layout with restrained charcoal, white, green status, amber caution, and red danger tokens. Navigation is persistent, detection controls remain above the fold, charts use labels as well as color, keyboard focus is visible, and motion respects `prefers-reduced-motion`. Cards are used only for discrete metrics or tools and are not nested.

## Verification And Deliverables

Automated tests cover fatigue classification, configuration, health, upload validation, and desktop process utilities. Browser checks cover dashboard, batch images, video, camera error state, history, and warning display. Delivery includes source, model placement instructions, Windows build scripts, Docker files, sample inputs, a concise Chinese user guide, and an演示 checklist. Model accuracy or YOLO12 training claims are explicitly excluded.
