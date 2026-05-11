# Tasks

## Task List

- [x] 1. Create the `cafe` Django app scaffold
  - [x] 1.1 Run `python manage.py startapp cafe` to generate the app skeleton
  - [x] 1.2 Add `'cafe'` to `INSTALLED_APPS` in `gymapp/settings.py`
  - [x] 1.3 Register `path('cafe/', include('cafe.urls'))` in `gymapp/urls.py`

- [x] 2. Define data models
  - [x] 2.1 Implement `MenuItem` model in `cafe/models.py` with `name`, `price`, and `is_active` fields
  - [x] 2.2 Implement `Order` model in `cafe/models.py` with `table_number`, `status`, `created_at`, `fulfilled_at`, and `payment_received_at` fields
  - [x] 2.3 Implement `OrderItem` model in `cafe/models.py` with `order` FK, `menu_item` nullable FK, `name` snapshot field, `unit_price`, and `quantity` fields
  - [x] 2.4 Add `total` property to `Order` and `subtotal` property to `OrderItem`
  - [x] 2.5 Generate and apply initial migration: `python manage.py makemigrations cafe && python manage.py migrate`

- [x] 3. Register models in Django admin
  - [x] 3.1 Register `MenuItem`, `Order`, and `OrderItem` in `cafe/admin.py` with appropriate list displays and inline support

- [x] 4. Implement views
  - [x] 4.1 Implement `CafeView` (GET `/cafe/`) in `cafe/views.py` using `StaffRequiredMixin`, fetching active orders, history orders, and menu items
  - [x] 4.2 Implement `CreateOrderView` (POST `/cafe/orders/create/`) with validation for non-empty table number and at least one item with quantity > 0
  - [x] 4.3 Implement `UpdateOrderStatusView` (POST `/cafe/orders/<id>/status/`) accepting `{"action": "fulfill" | "payment_received"}`, enforcing valid transitions, and returning JSON
  - [x] 4.4 Define URL patterns in `cafe/urls.py` for all three views

- [x] 5. Build the cafe template
  - [x] 5.1 Create `templates/cafe/cafe.html` extending `base.html` with the order entry form section
  - [x] 5.2 Add the Active Orders Board section with order cards showing ID, table number, items, time placed, and status badge
  - [x] 5.3 Add status action buttons ("Mark Fulfilled" for pending, "Mark Payment Received" for fulfilled) that call `UpdateOrderStatusView` via `fetch()` and update the card DOM on success
  - [x] 5.4 Add the Order History section showing today's `payment_received` orders sorted by payment timestamp descending
  - [x] 5.5 Add empty-state messages for both the active board and history section
  - [x] 5.6 Apply correct badge classes: `badge-active` for `pending`, `badge-suspended` for `fulfilled`, `badge-expired` for `payment_received`
  - [x] 5.7 Implement JavaScript for dynamic add/remove of order item rows in the entry form

- [x] 6. Add Cafe sidebar navigation link
  - [x] 6.1 Add a "Cafe" `<a>` link to the Main navigation section in `templates/base.html`, with the `active` class applied when `'/cafe' in request.path`

- [x] 7. Write tests
  - [x] 7.1 Write model unit tests for `MenuItem.__str__`, `OrderItem.subtotal`, `Order.total`, and default `Order.status`
  - [x] 7.2 Write view example tests: GET /cafe/ returns 200 for authenticated user; redirects to login for unauthenticated user
  - [x] 7.3 Write view example tests: valid POST to create order creates an Order and redirects; invalid POSTs (empty table, no items) do not create an Order
  - [x] 7.4 Write view example tests: fulfill action on pending order returns 200 and updates status; payment action on fulfilled order returns 200 and updates status; invalid transitions return 400
  - [x] 7.5 Write property-based tests using Hypothesis for Property 1 (order creation adds to active board) — Feature: cafe-management, Property 1
  - [x] 7.6 Write property-based tests using Hypothesis for Property 2 (empty table number rejected) and Property 3 (empty item list rejected) — Feature: cafe-management, Properties 2–3
  - [x] 7.7 Write property-based tests using Hypothesis for Property 4 (pending→fulfilled transition) and Property 5 (fulfilled→payment_received transition) — Feature: cafe-management, Properties 4–5
  - [x] 7.8 Write property-based tests using Hypothesis for Property 6 (invalid transitions rejected) — Feature: cafe-management, Property 6
  - [x] 7.9 Write property-based tests using Hypothesis for Property 7 (payment_received orders leave active board) and Property 8 (payment_received orders appear in history) — Feature: cafe-management, Properties 7–8
  - [x] 7.10 Write property-based tests using Hypothesis for Property 9 (subtotal calculation) — Feature: cafe-management, Property 9
  - [x] 7.11 Write property-based tests using Hypothesis for Property 10 (active orders sort order) and Property 11 (history sort order) — Feature: cafe-management, Properties 10–11
  - [x] 7.12 Add `hypothesis` to `requirements.txt`

- [-] 8. Seed initial menu items
  - [ ] 8.1 Create a data migration in `cafe/migrations/` that seeds a small set of default `MenuItem` records (e.g., coffee, tea, water, snacks) so the system is usable immediately after deployment
