# Severe Fatigue Notification Design

## Goal

Replace the blocking severe-fatigue dialog with a macOS-style notification in the upper-right corner so detection and video playback continue without user acknowledgement.

## Interaction

- Show the notification when a source first enters `severe` state.
- Do not repeat it for every severe frame. Re-arm only after that source returns to a non-severe state.
- Keep the notification visible for eight seconds, then dismiss it automatically.
- Allow immediate dismissal with an accessible icon button.
- Never move keyboard focus or add a page-blocking backdrop.

## Presentation

The notification is fixed below the top bar at the upper-right, with a compact warning icon, title, safety guidance, close control, and progress indicator. It uses the existing semantic red palette, a restrained shadow, and short slide/fade transitions. Reduced-motion preferences disable movement.

## Verification

Node tests cover state deduplication, re-arming, auto-dismissal, and manual dismissal. Flask page tests verify alert semantics and the absence of a modal dialog. Browser inspection confirms placement and that the detection workspace remains interactive.
