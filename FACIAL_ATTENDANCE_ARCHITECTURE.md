# Facial Attendance System — Architecture & Workflow

## Overview

Members check in by standing in front of a camera.
The system detects the face, checks it's a real person (anti-spoof),
extracts a 512-number fingerprint of the face, and matches it against
stored profiles — all in one HTTP request (~0.5–1.5 seconds on CPU).

---

## System Layers

```
BROWSER
  Camera → Canvas → Base64 JPEG → POST every 3s
      ↓
DJANGO VIEW  (attendance/views.py)
  Validation → Scan lock → face_service
      ↓
FACE SERVICE  (face_service.py)
  Decode → Detect → Anti-spoof → Embed
      ↓
MATCHER  (face_service.py)
  Cosine similarity vs stored embeddings
      ↓
DATABASE  (SQLite)
  Member.face_descriptor  — stored embeddings
  Attendance              — check-in records
```

---

## Phase 1 — Frontend Capture (attendance.html)

Every 3 seconds:

```
1. isScanning guard — if True, skip this tick (no overlapping requests)
2. Draw video frame to hidden <canvas>
3. Encode: canvas.toDataURL('image/jpeg', 0.7)
   └─ 0.7 quality = ~90KB  (was 0.95 = ~180KB, reduced for speed)
4. POST /attendance/checkin/
   Body: { "image": "<base64 string>" }
5. Handle response (see Phase 6)
```

---

## Phase 2 — Request Validation (attendance/views.py → checkin_api)

```
1. Must be POST                    → else 405
2. Parse JSON body                 → JSONDecodeError caught → 400
3. image field present             → else 400
4. Base64 decode                   → Exception caught → 400
5. Acquire _scan_lock (non-blocking)
   └─ Already locked (busy)?       → return status:'busy' immediately
   └─ Prevents concurrent ML work
6. Call face_service.extract_embedding(image_bytes)
   └─ Lock released in finally block regardless of outcome
```

---

## Phase 3 — Face Processing (face_service.py → extract_embedding)

```
A. InsightFace available?
   └─ No  → status:'unavailable'  (no crash, manual check-in still works)

B. Load model singleton (_get_face_app)
   └─ Model: buffalo_m
      - Detector:   SCRF-2.5G (lighter than buffalo_l SCRF-10G)
      - Recognizer: ResNet50 @ WebFace600K
      - det_size:   320×320  (was 640×640, ~2x faster)
   └─ Load failure → sentinel False set, no retry on next call
   └─ Returns None → status:'unavailable'

C. Decode image
   └─ cv2.imdecode(bytes) — corrupt data → status:'error'

D. Face detection
   └─ app.get(img) → list of faces
   └─ No faces     → status:'no_face'  (silent on frontend, retries next frame)
   └─ Many faces   → pick largest by bounding box area

E. Liveness / Anti-spoof check
   └─ Model: MiniFASNetV2-SE (static/antispoof/antispoof.onnx)
   └─ Crop face region with 20% padding → resize to 128×128

   ╔══════════════════════════════════════╗
   ║   LIVENESS THRESHOLD:  0.45          ║
   ║                                      ║
   ║   score = softmax(model_output)[1]   ║
   ║   index 1 = "real" class             ║
   ║                                      ║
   ║   score >= 0.45 → REAL  → continue  ║
   ║   score <  0.45 → SPOOF → blocked   ║
   ╚══════════════════════════════════════╝

   └─ Any exception in liveness → FAIL OPEN (True, 1.0)
      A code bug never blocks a real person

F. Extract embedding
   └─ face.normed_embedding — 512-dim float32 vector
   └─ L2-normalized so dot product == cosine similarity
   └─ Return status:'ok' + embedding + liveness_score
```

---

## Phase 4 — Identity Matching (face_service.py → find_best_match)

```
Input: 512-dim probe vector

1. For every Member with face_descriptor in DB:
   Each member stores up to 5 embeddings (5 enrollment angles)
   
   For each stored embedding:
     └─ Shape mismatch → skip silently (different model version)
     └─ score = dot(probe, stored)  — cosine similarity [-1, 1]
     └─ Track highest score + member_id

   ╔══════════════════════════════════════╗
   ║   RECOGNITION THRESHOLD:  0.40       ║
   ║                                      ║
   ║   score >= 0.40 → Match found       ║
   ║   score <  0.40 → Unknown face      ║
   ║                                      ║
   ║   Typical scores:                    ║
   ║   Same person, good angle: 0.6–0.9  ║
   ║   Same person, bad angle:  0.4–0.6  ║
   ║   Different person:        0.0–0.3  ║
   ╚══════════════════════════════════════╝

2. No match → status:'unknown'
3. Match found → return (member_id, score)
```

---

## Phase 5 — Status Checks & Record Creation (attendance/views.py)

```
1. Fetch Member object from DB
   └─ Not found → 404

2. sync_expired_statuses() — recalculate active/expired before deciding

3. Status check order (PRIORITY):
   a. member.is_flagged     → status:'flagged'    (explicit admin block)
   b. status == 'suspended' → status:'suspended'
   c. status == 'expired'   → status:'expired'

4. All checks passed → create attendance record:
   Attendance(member=member, date=today, method='face')
   └─ unique_together('member', 'date') — one check-in per day enforced at DB
   └─ IntegrityError caught → status:'duplicate' (409)

5. Success → status:'ok' + member_name + member_id + score
```

---

## Phase 6 — Frontend Response Handling

| Response status | What the user sees | Behaviour |
|---|---|---|
| `ok` | Green overlay: name + time + "Attendance Recorded" | Added to today's list, scan resumes after 3s |
| `duplicate` | Info bar: "already checked in today" | Continues scanning |
| `no_face` | Nothing | Silent, tries next frame |
| `spoof` | Red overlay: "Liveness check failed" | 2.5s overlay, continues scanning |
| `unknown` | Result bar: "Face not recognised" | Continues scanning |
| `expired` | Error bar + member name | 15s cooldown for that member |
| `suspended` | Error bar + member name | 15s cooldown for that member |
| `flagged` | Error bar + member name | 15s cooldown for that member |
| `busy` | Nothing | Server was processing another frame, silent |
| `error` | Status bar updates | Continues scanning |

---

## Enrollment Workflow (Member Registration)

```
5 captures, each at a different angle:
  Straight → Left → Right → Up → Down

Each capture:
  POST /members/enroll-frame/ → extract_embedding_for_enrollment()
  └─ Same pipeline BUT no liveness check
     (staff-controlled environment, trusted)
  └─ Returns 512-dim embedding

All 5 stored as: Member.face_descriptor = [[e1],[e2],[e3],[e4],[e5]]

Why 5 angles?
  Recognition threshold 0.4 is met more reliably when the member
  approaches the camera at any slight angle — not just straight on.
```

---

## All Thresholds at a Glance

| Setting | Value | Where | Lower it to... | Raise it to... |
|---|---|---|---|---|
| Liveness (anti-spoof) | **0.45** | `face_service.py` LIVENESS_THRESHOLD | Let more people through (risk: spoofs) | Be stricter (risk: false blocks) |
| Recognition match | **0.40** | `find_best_match()` threshold param | Accept lower-confidence matches | Require stronger match |
| Scan interval | **3000ms** | `attendance.html` SCAN_INTERVAL | Scan faster (more CPU) | Scan slower |
| Duplicate cooldown | **10s** | `attendance.html` lastCheckedIn | — | Prevent re-scan longer |
| Suspended/expired cooldown | **15s** | `attendance.html` setTimeout | — | Prevent re-scan longer |

---

## Required Files

| File | Location | Size | What it does |
|---|---|---|---|
| buffalo_m model | `~/.insightface/models/buffalo_m/` | ~150MB | Face detection + 512-dim embedding |
| antispoof.onnx | `static/antispoof/antispoof.onnx` | ~1MB | Real vs fake face classification |

---

## Error Resilience Summary

| Failure | Handled by | Result |
|---|---|---|
| insightface not installed | INSIGHTFACE_AVAILABLE flag | Graceful unavailable, no crash |
| Model fails to load | Sentinel _face_app=False | No retry loop, server stays fast |
| Liveness model crashes | try/except in _check_liveness | Fails open — real person not blocked |
| Corrupt DB embedding | Per-iteration try/except in find_best_match | Bad record skipped, others matched |
| Two frames arrive simultaneously | _scan_lock non-blocking | Second frame rejected instantly |
| No member selected (manual check-in) | Empty member_id guard | Clean error message, no 500 |
| Bad date in URL filter | is_valid_date() validation | Invalid date ignored, no 500 |
