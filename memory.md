# Memory — Gym Management Web App (5 Star Fitness)

Session notes for continuity between work sessions. Last updated: 2026-08-03.

## What this project is
- Private single-gym Django app for a desktop (Windows) deployment.
- Face recognition is **server-side** (InsightFace buffalo_m, 512-d embeddings; descriptor may be a list of embeddings for multi-angle enrollment). Anti-spoof liveness enabled (`LIVENESS_THRESHOLD = 0.2`, lowered 2026-08-03 to accept more in poor lighting).
- Entry point: `main.py` → pywebview native window + background Django WSGI server.
- **Deployment model (decision):** ONE machine hosts the app (source of truth, `%APPDATA%\FiveStarFitness\db.sqlite3`). Office PCs reach it in a browser at `http://<front-desk-ip>:8765`. Server binds `0.0.0.0`; NO per-device SQLite copies.
- Scale: ~1000 members. Face inference 2–8s CPU is acceptable; matching must be ~10–20ms → now O(1) via cached numpy descriptor matrix.

## How to run / test (ALWAYS use the venv)
- `.\myenv\Scripts\python.exe manage.py runserver` (dev) — or run `main.py` for the desktop app.
- Full test suite: `.\myenv\Scripts\python.exe manage.py test` (currently **87 tests, all pass**).
- System check: `.\myenv\Scripts\python.exe manage.py check`.
- `myenv` has django 4.2.16 + full deps. Global Python 3.13 has only numpy/django (no django-environ) — do NOT use it for this project.
- Waitress `3.0.2` and pywebview `6.2.1` are installed in `myenv` (pywebview was missing from requirements until 2026-08-03 — now pinned).

## Completed work (P0 hardening, 2026-08-03)
1. **Member expiry clobbering fixed** — `members/models.py::Member.save()` derives expiry ONLY on create (`self._state.adding`) and only if `expiry_date` not explicitly provided; later saves never recompute.
2. **Payment/membership decoupled** — `billing/models.py::Payment.save()` no longer mutates membership. New `Payment.apply_to_membership()` (max-based extension, idempotent, never shortens), wired into all approve flows in `billing/views.py` (single, unflag, bulk). Payments extend expiry ONLY when approved.
3. **Attendance refactor** — single `check_in_time` DateTimeField + `date` DateField (bucketing/unique). `save()` derives local date. Check-in uses `get_or_create(member, date, defaults=...)` + IntegrityError race fallback.
4. **CASCADE → PROTECT** — `billing.Payment.member` and `attendance.Attendance.member` now PROTECT; `MemberDeleteView` catches `ProtectedError` → user-facing error (no 500).
5. **No hardcoded creds** — `main.py`/`runtime_hook.py` bootstrap `admin` with `secrets.token_urlsafe(12)` one-time password written to `admin_credentials.txt` in data dir, `profile.must_change_password=True`. `ForcePasswordChangeMiddleware` (accounts/middleware.py) blocks everything except login/logout/password/static/media until password changed. `ChangePasswordView` at `/accounts/password/`. NOTE: plaintext OTP in the file is a known first-run tradeoff.
6. **Liveness re-enabled** in `face_service.extract_embedding` (was commented out).
7. **LAN access** — `main.py`/`runtime_hook.py` bind `0.0.0.0`, auto-discover LAN IPs into `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS`.
8. **O(1) matching** — `face_service`: `_build_descriptor_matrix()`, `get_descriptor_matrix()` (30s TTL + lock), `invalidate_descriptor_cache()`; `find_best_match()` = `matrix @ probe` argmax; cache invalidated on descriptor writes/deletes. Handles both 128-d (tests) and 512-d (buffalo_m) descriptors.
9. **Tests rewritten** to real contracts (members/billing/attendance/accounts). 87 pass.
10. Migrations applied to real dev DB: `accounts/0002`, `attendance/0002` (with RunPython backfill combining legacy time + date), `billing/0003`. Verified on temp copy + real DB.

## Completed work (P1 hardening, 2026-08-03)
1. **Frontend resilience** — `templates/attendance/attendance.html`: catch-all `else` in the check-in status chain (no more frozen camera on unknown/400/404 responses), throttled "no face" hint for bad lighting, network-error status message; **live green detection box** overlay (`#fr-overlay`, aligned to the video's `object-fit:cover` crop via `drawFaceBox`) — never baked into the server frame.
2. **DOM XSS fixed** — `addCheckinToList` escapes member names (`esc()`) before `innerHTML`; server-rendered rows were already auto-escaped.
3. **checkin_api hardening** (`attendance/views.py`) — body cap `MAX_BODY_SIZE=2MB` / `MAX_IMAGE_SIZE=1.5MB` (413 before decode; `DATA_UPLOAD_MAX_MEMORY_SIZE` does NOT bound raw body); matching + business-rule section wrapped in `try/except` → graceful 200 error instead of 500 traceback; added `logging`.
4. **Login brute-force throttle** (`accounts/views.py`) — in-memory per-IP, 5 fails/15min → blocked (cooldown 15min) BEFORE any auth attempt; message shown via `messages` (added `{% if messages %}` block to `login.html`). Process-local (fine: waitress = single process).
5. **InsightFace load retry** (`face_service.py`) — `_get_face_app()` now retries after 60s cooldown instead of permanently setting `_face_app=False` (transient disk/ONNX hiccup no longer bricks face recognition until restart).
6. **Security headers** (`gymapp/settings.py`) — `SECURE_CONTENT_TYPE_NOSNIFF=True`, `SECURE_REFERRER_POLICY='same-origin'`. HSTS/secure cookies deliberately NOT set (plain-HTTP LAN would break).

## Open items / decisions
- **`gymapp.spec` is STALE/DUPLICATE.** Real build spec is `main.spec` (entry `main.py`, produces `dist/FiveStarFitness`). `gymapp.spec` packages `manage.py` → the exe would just print Django help (no server/webview). User said "fine for now" — do NOT delete without asking.
- `dist/FiveStarFitness` and `build/` contain an OLD build (pre-P0-fixes). Needs a fresh `pyinstaller --clean main.spec` for handover.
- `cafe/views.py` strftime fixed: `%I:%M %p` + `.lstrip('0')` (Windows `%-I` is invalid).

## Gotchas
- `.hypothesis/` and `staticfiles/` are generated (gitignored). `.gitignore` now includes `.hypothesis/`.
- Running `main.py` in dev runs `collectstatic --clear` → writes repo `staticfiles/` (gitignored, harmless) and creates `%APPDATA%\FiveStarFitness\`.
- `gymapp/views.py` and the deleted `REDESIGN_PROGRESS.md`/`SETUP_GUIDE.md` in git status are pre-existing uncommitted changes, NOT mine — leave alone.
- DPI/Windows: pywebview window uses WebView2. Console=True in spec (logs needed).
