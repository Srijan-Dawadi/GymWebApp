# VM Test Checklist — Five Star Fitness Client Install

Purpose: validate a fresh PyInstaller build on a clean Windows VM exactly like a real
client machine (no Python, no prior installs, no pre-downloaded models). Run once
with internet, then once offline, and record pass/fail per item.

## 1. Pre-build (on dev machine)
- [ ] Fresh build: `.\myenv\Scripts\python.exe -m PyInstaller --clean main.spec`
- [ ] Confirm `dist\FiveStarFitness\FiveStarFitness.exe` exists
- [ ] Spot-check bundle:
  - `_internal\models\buffalo_m\*.onnx` (5 files: det_2.5g, w600k_r50, 2d106det, 1k3d68, genderage)
  - `_internal\static\antispoof\antispoof.onnx`
  - `_internal\static\face-api\models\` (shard files present)
  - `_internal\staticfiles\` present
- [ ] Note exact bundle size (expect ~1–1.5 GB with models)

## 2. VM setup
- [ ] Clean Windows 10/11 VM (no Python, no gym app ever installed, no `~/.insightface`)
- [ ] Internet ON (simulates a real client first run)
- [ ] Leave UAC/SmartScreen as a real user would have
  - Note: unsigned exe → SmartScreen warning is expected ("More info → Run anyway")

## 3. First-run smoke test (internet ON)
- [ ] Launch exe → console shows migrations + admin bootstrap
- [ ] `%APPDATA%\FiveStarFitness\db.sqlite3` created
- [ ] `admin_credentials.txt` exists with one-time password
- [ ] WebView window opens to dashboard → login with OTP → forced password change → dashboard loads, charts render
- [ ] First face check-in: confirm the ~275 MB buffalo_m download from GitHub happens once
  (watch console / network). Known fragility point — verify it actually succeeds.

## 4. Functional matrix (internet ON)
- [ ] Face check-in → detection box appears, success overlay, record in Today's list
- [ ] Duplicate check-in → "already checked in" message
- [ ] Manual check-in
- [ ] Member create + face enrollment (photo upload / multi-angle)
- [ ] Billing: approve payment → expiry extends
- [ ] Attendance history: filter, pagination, CSV export
- [ ] Dashboard charts (Chart.js via CDN)
- [ ] Date pickers (flatpickr via CDN)
- [ ] Cafe / inventory flows
- [ ] Second LAN PC: browse to `http://<server-ip>:8765`, login, POST a manual check-in
  (validates LAN bind + CSRF trusted origins)

## 5. Offline test (disconnect VM internet)
- [ ] Reboot VM, launch app offline
- [ ] Server-side face recognition works (models cached in `~/.insightface` from step 3)
- [ ] Detection box + UI styling expected to FAIL (CDN Tailwind / face-api.js) — document as known limitation
- [ ] Manual check-in + attendance history work
- [ ] Admin login works offline

## 6. Persistence
- [ ] Reboot → data intact (members / attendance / billing)
- [ ] DB backup/restore test: copy `db.sqlite3` → wipe → restore → app boots with data

## 7. Report back
- [ ] Pass / fail per item, exact error messages, bundle size, first-check-in download time

## Known risks to watch
- First-run model download depends on GitHub being reachable; if blocked by firewall,
  face recognition fails even with internet. The `INSIGHTFACE_HOME` fix (use bundled
  models) removes this dependency.
- `dist/FiveStarFitness` and `build/` currently hold a pre-P0-fixes build — must rebuild
  fresh before this test means anything.
- Bundling of cv2 / onnxruntime / insightface native libs only truly verifies on this VM.
