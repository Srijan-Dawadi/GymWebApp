# Implementation Plan: Gym Management Web Application

## Overview

Incremental implementation of the Django gym management system. Each task builds on the previous, starting with project scaffolding and ending with deployment configuration. Testing tasks are sub-tasks placed close to the code they validate.

## Tasks

- [x] 1. Project scaffolding and configuration
  - Create Django project `gymapp` with apps: `accounts`, `members`, `billing`, `attendance`
  - Configure `settings.py` with environment variable support (`python-decouple` or `django-environ`): `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`
  - Configure SQLite for dev and PostgreSQL for prod via `DATABASE_URL`
  - Install and configure Tailwind CSS via `django-tailwind` or CDN link in base template
  - Set up WhiteNoise for static file serving in production
  - Create `base.html` template with sidebar + top navbar layout, toast notification container, and Tailwind CDN
  - Configure `MEDIA_ROOT` and `MEDIA_URL` for member photo uploads
  - _Requirements: 9.1, 9.2, 10.1, 10.2, 10.3_

- [x] 2. Accounts app — authentication and roles
  - [x] 2.1 Implement `Profile` model with `user` (OneToOne) and `role` (`admin`/`staff`) fields; create and run migration
    - Wire `post_save` signal to auto-create `Profile` when a `User` is created
    - _Requirements: 1.6_
  - [x] 2.2 Implement login view using Django's `AuthenticationForm`, logout view, and URL routes at `/accounts/login/` and `/accounts/logout/`
    - Redirect authenticated users to `/dashboard/` on login
    - _Requirements: 1.1, 1.2, 1.7_
  - [x] 2.3 Implement `AdminRequiredMixin` and `StaffRequiredMixin` class-based view mixins
    - `AdminRequiredMixin`: deny with 403 if `request.user.profile.role != 'admin'`
    - `StaffRequiredMixin`: redirect to login if unauthenticated; allow both roles
    - Apply `login_required` decorator / mixin to all protected views
    - _Requirements: 1.3, 1.4, 1.5_
  - [ ]* 2.4 Write property test for role-based access control
    - **Property: Admin access** — for any admin user, all protected URLs return 200
    - **Property: Staff restriction** — for any staff user, admin-only URLs return 403
    - **Validates: Requirements 1.3, 1.4**
  - [ ]* 2.5 Write unit tests for authentication flows
    - Test valid login redirects to dashboard
    - Test invalid login stays on login page with error
    - Test unauthenticated access redirects to login
    - _Requirements: 1.1, 1.2, 1.5_

- [x] 3. Members app — models and CRUD
  - [x] 3.1 Implement `MembershipPlan` model (`name`, `price`, `duration_days`) and `Member` model (all fields per design); create and run migrations
    - _Requirements: 2.5, 4.1_
  - [x] 3.2 Implement member list view (`/members/`) with pagination and name/email search filter
    - _Requirements: 3.1, 3.2_
  - [x] 3.3 Implement member detail view (`/members/<id>/`) showing full profile, payment history, and attendance history
    - _Requirements: 3.5_
  - [x] 3.4 Implement member edit view (`/members/<id>/edit/`) with form validation; on save, recalculate `expiry_date` and `status`
    - _Requirements: 3.3, 2.6, 2.7_
  - [x] 3.5 Implement member delete view (`/members/<id>/delete/`) with cascade delete of attendance records
    - _Requirements: 3.4_
  - [ ]* 3.6 Write property test for expiry date derivation
    - **Property 1: Expiry date derivation invariant**
    - For any `join_date` and `duration_days`, assert `member.expiry_date == join_date + timedelta(days=duration_days)`
    - Use `hypothesis` with `@given(dates(), integers(min_value=1, max_value=3650))`
    - **Validates: Requirements 2.6**
  - [ ]* 3.7 Write property test for status derivation
    - **Property 3: Status reflects expiry date**
    - For any `expiry_date`, assert `status == 'active'` iff `expiry_date > date.today()`
    - Use `hypothesis` with `@given(dates())`
    - **Validates: Requirements 2.7, 5.3**
  - [ ]* 3.8 Write property test for cascade delete
    - **Property: Cascade delete** — for any member with N attendance records, deleting the member results in 0 attendance records for that member
    - **Validates: Requirements 3.4**
  - [ ]* 3.9 Write unit tests for member search and member detail
    - Test search by name returns only matching members
    - Test search by email returns only matching members
    - Test member detail page contains payment and attendance history
    - _Requirements: 3.2, 3.5_

- [x] 4. Member registration with face capture
  - [x] 4.1 Implement member registration view (`/members/add/`) with a Django form that accepts all required fields including `face_descriptor` as a hidden JSON field
    - On POST: validate form, calculate `expiry_date = join_date + timedelta(days=plan.duration_days)`, set `status`, save member
    - Reject duplicate emails with a form validation error
    - _Requirements: 2.5, 2.6, 2.7, 2.8_
  - [x] 4.2 Add face capture UI to the registration template
    - Load face-api.js from CDN; load `ssdMobilenetv1`, `faceLandmark68Net`, `faceRecognitionNet` models from `/static/face-api/models/`
    - Activate webcam via `getUserMedia()` and display live video in a `<video>` element
    - On "Capture Face" button click: run `detectSingleFace().withFaceLandmarks().withFaceDescriptor()`
    - On success: populate the hidden `face_descriptor` input with `JSON.stringify(Array.from(descriptor))`
    - On failure: show inline error "No face detected. Please try again." and block form submission
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 4.3 Download and place face-api.js model files into `static/face-api/models/` directory
    - Required files: `ssd_mobilenetv1_model-weights_manifest.json` + shard files, `face_landmark_68_model-weights_manifest.json` + shard files, `face_recognition_model-weights_manifest.json` + shard files
    - _Requirements: 7.1_
  - [ ]* 4.4 Write property test for face descriptor round-trip
    - **Property 5: Face descriptor round-trip**
    - For any list of 128 floats, `json.loads(json.dumps(descriptor)) == descriptor`
    - Use `hypothesis` with `@given(lists(floats(allow_nan=False, allow_infinity=False), min_size=128, max_size=128))`
    - **Validates: Requirements 2.3**
  - [ ]* 4.5 Write unit tests for registration form validation
    - Test duplicate email returns validation error
    - Test missing `face_descriptor` returns validation error
    - Test valid submission creates member with correct `expiry_date`
    - _Requirements: 2.5, 2.8_

- [ ] 5. Checkpoint — Ensure all tests pass
  - Run `python manage.py test` and verify all tests pass. Ask the user if any questions arise.

- [x] 6. Billing app — plans and payments
  - [x] 6.1 Implement `MembershipPlan` CRUD views: list/create at `/billing/plans/`, edit at `/billing/plans/<id>/edit/`
    - On delete attempt: check if any `Member` references the plan; if yes, return error response without deleting
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 6.2 Implement `Payment` model (`member`, `amount`, `date_paid`, `period_start`, `period_end`, `payment_method`, `notes`); create and run migration
    - _Requirements: 5.1_
  - [x] 6.3 Implement payment recording view (`/billing/payments/add/`)
    - On save: update `member.expiry_date = payment.period_end` and recalculate `member.status`
    - _Requirements: 5.2, 5.3_
  - [x] 6.4 Implement payment list view (`/billing/payments/`) with filter by member and date range
    - _Requirements: 5.4_
  - [x] 6.5 Implement overdue members queryset: `Member.objects.filter(expiry_date__lt=date.today())`; expose on a dedicated overdue list page or dashboard widget
    - _Requirements: 5.5_
  - [ ]* 6.6 Write property test for payment updates expiry date
    - **Property 2: Payment updates expiry date**
    - For any member and any `period_end` date, after recording a payment, `member.expiry_date == period_end`
    - Use `hypothesis` with `@given(dates())`
    - **Validates: Requirements 5.2**
  - [ ]* 6.7 Write property test for overdue member detection
    - **Property 8: Overdue member detection**
    - For any set of members with random `expiry_date` values, the overdue queryset contains exactly those with `expiry_date < date.today()`
    - Use `hypothesis` with `@given(lists(dates()))`
    - **Validates: Requirements 5.5**
  - [ ]* 6.8 Write property test for monthly revenue calculation
    - **Property 7: Monthly revenue calculation**
    - For any set of payments with random `date_paid` values, the revenue sum equals the sum of `amount` for payments in the current month
    - Use `hypothesis` with `@given(lists(...))`
    - **Validates: Requirements 5.6**
  - [ ]* 6.9 Write unit test for plan deletion protection
    - Test that deleting a plan with active members returns an error and does not delete the plan
    - _Requirements: 4.3_

- [x] 7. Attendance app — check-in API and manual fallback
  - [x] 7.1 Implement `Attendance` model (`member`, `check_in_time`, `date`, `method`) with `unique_together = ('member', 'date')`; create and run migration
    - _Requirements: 6.8, 6.9_
  - [x] 7.2 Implement `POST /attendance/checkin/` JSON endpoint
    - Accept `{member_id: int}` in request body
    - Validate member exists (404 if not)
    - Check for existing `Attendance` record for today (return 409 if duplicate)
    - Create `Attendance` record with `method='face'`
    - Return `{status: "ok", member_name: "..."}` on success
    - _Requirements: 6.4, 6.8, 6.9_
  - [x] 7.3 Implement manual check-in form on the attendance page
    - Staff selects member from dropdown and submits; creates `Attendance` record with `method='manual'`
    - _Requirements: 6.6, 6.10_
  - [x] 7.4 Implement attendance list view (`/attendance/`) showing today's check-ins and a full history table
    - _Requirements: 8.3_
  - [ ]* 7.5 Write property test for no duplicate daily check-in
    - **Property 4: No duplicate daily check-in**
    - For any member, sending multiple POST requests to `/attendance/checkin/` on the same date results in exactly one `Attendance` record
    - Use `hypothesis` with `@given(integers(min_value=2, max_value=20))` for number of attempts
    - **Validates: Requirements 6.8**
  - [ ]* 7.6 Write unit tests for check-in endpoint
    - Test valid check-in creates Attendance with method='face'
    - Test duplicate check-in returns 409
    - Test invalid member_id returns 404
    - Test manual check-in creates Attendance with method='manual'
    - _Requirements: 6.9, 6.10_

- [x] 8. Face descriptors API endpoint
  - [x] 8.1 Implement `GET /members/descriptors/` JSON endpoint
    - Return `[{id, full_name, face_descriptor}]` for all members with a non-null `face_descriptor`
    - Require authentication; accessible to both Admin and Staff
    - _Requirements: 6.1_
  - [ ]* 8.2 Write property test for descriptor cache completeness
    - **Property 9: Descriptor cache completeness**
    - For any set of members in the DB, the `/members/descriptors/` response contains exactly one entry per member with a non-null descriptor, with no duplicates
    - Use `hypothesis` with `@given(lists(...))`
    - **Validates: Requirements 6.1**

- [x] 9. Facial recognition attendance UI
  - Implement the attendance page template (`/attendance/`) with:
    - A `<video>` element for the live webcam feed
    - A status banner showing model loading progress ("Loading models...", "Ready")
    - JavaScript that: loads all three face-api.js models from `/static/face-api/models/`, calls `getUserMedia()`, runs detection loop every 1000ms using `setInterval`, calls `FaceMatcher.findBestMatch()` against descriptors fetched from `/members/descriptors/`, POSTs to `/attendance/checkin/` on match, shows ✅ or ❌ toast notifications
    - Graceful error handling: if models fail to load, show error banner and disable webcam; if camera permission denied, show instructions
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.2, 7.3, 7.4_

- [x] 10. Dashboard
  - [x] 10.1 Implement dashboard view (`/dashboard/`) with context variables:
    - `total_members = Member.objects.count()`
    - `active_members = Member.objects.filter(status='active').count()`
    - `today_attendance = Attendance.objects.filter(date=date.today()).count()`
    - `monthly_revenue = Payment.objects.filter(date_paid__year=today.year, date_paid__month=today.month).aggregate(Sum('amount'))['amount__sum'] or 0`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [ ]* 10.2 Write unit tests for dashboard metrics
    - Test total_members count matches DB
    - Test active_members count matches filtered DB
    - Test today_attendance count matches today's records
    - Test monthly_revenue sum matches current-month payments
    - _Requirements: 8.1, 8.2, 8.3, 5.6_

- [x] 11. CSV export
  - [x] 11.1 Implement `GET /attendance/export/` view (Admin only)
    - Accept optional `start` and `end` query params (ISO date strings)
    - Return a `StreamingHttpResponse` with `Content-Type: text/csv`
    - CSV columns: `member_name`, `date`, `check_in_time`, `method`
    - Filter by date range if params provided
    - _Requirements: 8.5, 8.6_
  - [ ]* 11.2 Write property test for CSV export completeness
    - **Property 10: CSV export completeness**
    - For any set of attendance records and any date range `[start, end]`, the CSV response contains exactly the records with `date` in `[start, end]`
    - Use `hypothesis` with `@given(lists(...), dates(), dates())`
    - **Validates: Requirements 8.5, 8.6**

- [ ] 12. Checkpoint — Ensure all tests pass
  - Run `python manage.py test` and verify all tests pass. Ask the user if any questions arise.

- [x] 13. UI polish and toast notifications
  - Add JavaScript toast notification system to `base.html` (pure JS, no library required)
  - Wire Django messages framework to render as toasts on page load
  - Add loading spinner component for pages that fetch data
  - Ensure sidebar highlights the active page link
  - Verify layout is responsive at 375px, 768px, and 1280px breakpoints
  - _Requirements: 9.3, 9.4, 9.5_

- [x] 14. Deployment configuration
  - Add `Procfile` for Railway/Render: `web: gunicorn gymapp.wsgi`
  - Add `requirements.txt` with all dependencies including `gunicorn`, `psycopg2-binary`, `whitenoise`, `Pillow`, `hypothesis`
  - Add `.env.example` documenting all required environment variables
  - Configure `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
  - Ensure `DEBUG=False` renders a custom 403/404/500 error template without stack traces
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 15. Final checkpoint — Ensure all tests pass
  - Run `python manage.py test` and `python manage.py collectstatic --noinput`. Verify everything passes. Ask the user if any questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use the `hypothesis` library (`pip install hypothesis`)
- Each property test references its design document property number in a comment: `# Feature: gym-management, Property N: <text>`
- face-api.js model files must be downloaded separately and placed in `static/face-api/models/` before running the app
- The `unique_together` constraint on `Attendance` enforces the no-duplicate-check-in rule at the database level as a safety net
