# SMS Service Plan — Member Expiry Reminders

Status: **Planned** (not yet implemented)
Provider: **Sparrow SMS** (Nepal)
Scheduling: **In-app daily thread** in `main.py`
Message language: **English**
Recipients: active members only (skip suspended / flagged)

---

## Goal

Automatically send an SMS to members' mobile numbers (Nepal SIMs) when their
membership is **3 days from expiring** and when it **expires today**.

- Bucket 1 (3-day): active members with `expiry_date == today + 3`
- Bucket 2 (today): active members with `expiry_date == today`
- Message example (English):
  `Dear Ankit, your Five Star Fitness membership expires on 2026-08-05. Please renew. - Five Star Fitness`

---

## Decisions (confirmed)

| Topic | Choice |
|---|---|
| SMS gateway | Sparrow SMS (sparrowsms.com) |
| Scheduling | In-app background thread, once daily at `SMS_SEND_TIME` (default 09:00) |
| Language | English |
| Suspended/flagged | Skipped (only `status == 'active'` get reminders) |
| Duplicate sends | Prevented via `SMSLog` unique constraint per member+type+day |
| Invalid phones | Skipped (only 10-digit Nepal numbers, `97x` / `98x`, accepted) |
| Provider setup | Not included — needs Sparrow account, API token, NTA-approved sender ID |

---

## Provider notes (Sparrow SMS API)

- Sign up at https://sparrowsms.com (requires business verification: company
  registration, PAN, letter of intent → NTA-approved Sender ID).
- Send: `POST https://api.sparrowsms.com/v2/sms/` (or per current docs at
  https://docs.sparrowsms.com/)
  - Params: `token` (API token), `from` (approved sender ID), `to`
    (10-digit number, comma-separated for bulk), `text` (URL-encoded).
- Credit check: `GET .../credit/` (optional, log a warning when low).
- Known response codes: `1002` invalid token, `1008` invalid sender,
  `1011` invalid receiver, `1013` insufficient credits.
- Direct NTC/Ncell connectivity; credits-based pricing, no expiry on credits.

---

## Tasks

### 1. New `notifications` Django app

- Create `notifications/` with `apps.py`, `models.py`, `admin.py`,
  `sms.py`, `migrations/`, `management/commands/send_expiry_reminders.py`,
  `tests.py`, `__init__.py`.
- Register in `INSTALLED_APPS` (`gymapp/settings.py`).

### 2. `SMSLog` model (`notifications/models.py`)

- Fields:
  - `member` FK → `members.Member` (`on_delete=CASCADE`, `related_name='sms_logs'`)
  - `notification_type` = `expiry_3day` | `expiry_today`
  - `phone` CharField (number actually attempted)
  - `status` = `sent` | `failed`
  - `error` TextField(blank)
  - `sent_at` DateTimeField(auto_now_add)
- `UniqueConstraint(fields=['member', 'notification_type', 'sent_at__date'])` —
  note: Django constraints can't use date transforms; use a `date` DateField
  populated at send time instead, and constraint on
  `['member', 'notification_type', 'date']`.
- Register in `notifications/admin.py`.

### 3. SMS service (`notifications/sms.py`)

- `send_sms(to: str, text: str) -> dict` returning `{'ok': bool, 'error': str|None}`.
- Uses `requests.post` to the Sparrow endpoint with `token`, `from`, `to`, `text`.
- `normalize_phone(raw) -> str | None`:
  - strip spaces/`+977`, drop leading `977`, accept exactly 10 digits starting `97`/`98`.
  - return `None` for anything else (e.g. existing junk like `4545`).
- Never raises — catch network/HTTP/parse errors and return failure.
- Honor `SMS_ENABLED`; when disabled, log and return `{'ok': False, 'error': 'disabled'}`.
- Optional: `check_credit()` logging a warning when low.

### 4. Management command `send_expiry_reminders`

- Bucket queries (both filter `status='active'`, exclude `is_flagged=True`):
  - 3-day: `expiry_date == date.today() + timedelta(days=3)` → type `expiry_3day`
  - today: `expiry_date == date.today()` → type `expiry_today`
- For each member: skip if `normalize_phone(phone)` is `None`;
  skip if `SMSLog` already exists for (member, type, today);
  compose message; `send_sms`; write `SMSLog` (sent or failed).
- Flags:
  - `--dry-run`: print recipient / phone / message, send nothing, write nothing.
  - `--force`: send even if already sent today (bypass dedup) — for manual retries.
- Exit cleanly with a summary: `N sent, M failed, K skipped`.

### 5. Settings (`gymapp/settings.py`)

- Add (via `django-environ`, matching existing style):
  - `SMS_ENABLED` (bool, default `False`)
  - `SMS_TOKEN` (default `''`)
  - `SMS_SENDER_ID` (default `''`)
  - `SMS_API_URL` (default Sparrow endpoint)
  - `SMS_SEND_TIME` (default `'09:00'`)
- App must still run with empty SMS config (guards in the service/command).

### 6. `.env.example`

- Add:
  ```
  SMS_ENABLED=False
  SMS_TOKEN=
  SMS_SENDER_ID=
  SMS_SEND_TIME=09:00
  ```

### 7. In-app scheduler (`main.py`)

- After server start, spawn a daemon thread.
- Loop every ~60s; when current time `>= SMS_SEND_TIME` and the command
  hasn't run today (track last-run date in-memory, plus `SMSLog` dedup as
  the source of truth), call
  `call_command('send_expiry_reminders', verbosity=1)`.
- If the app opens after the target time, fire on startup.
- Uses `django.core.management.call_command` so the logic lives only in
  the command.

### 8. `requirements.txt`

- Add `requests`.

### 9. Tests (`notifications/tests.py`)

- Recipient selection: 3-day, today, expired, suspended, flagged buckets.
- Invalid phone skipped (`4545`, 9-digit, non-97/98).
- Dedup: same (member, type, day) not re-sent.
- Send success and failure paths (mock the HTTP call / service).
- Command `--dry-run` writes no `SMSLog` and performs no HTTP.

### 10. Documentation (`SETUP_GUIDE.md`)

- Add "SMS Reminders" section:
  - Sparrow signup + business verification + sender ID approval steps.
  - Fill `.env` (`SMS_ENABLED=True`, token, sender ID, send time).
  - Verify with `python manage.py send_expiry_reminders --dry-run`.
  - How to check `SMSLog` history in Django admin.

---

## Verification

1. `python manage.py makemigrations notifications && python manage.py migrate`
2. `python manage.py check`
3. `python manage.py test notifications` (and full suite)
4. `python manage.py send_expiry_reminders --dry-run` against a real DB
5. With real credentials: confirm an actual SMS is received on a test number

---

## Out of scope (later)

- Wiring the placeholder "Remind" button in `members/list.html:325`
  to send a manual reminder to selected members.
- Payment/billing reminders (reuse `SMSLog` + command pattern).
- Delivery-report webhooks.
