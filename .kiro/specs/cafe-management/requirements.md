# Requirements Document

## Introduction

The Cafe Management feature adds a new "Cafe" tab to the existing 5 Star Fitness gym management system. It provides a simple order-entry workflow for the gym's in-house cafe. A waiter takes orders on paper (with a table number), and a receptionist enters them into the system via the new tab. The system tracks each order through two lifecycle stages — Fulfilled and Payment Received — and maintains a daily history of completed orders. The feature integrates seamlessly into the existing Django application, reusing the same database, session, authentication, and Tailwind/Spotify-dark UI design system.

---

## Glossary

- **Cafe_System**: The cafe management module added to the gym management application.
- **Order**: A record representing one table's request for one or more menu items, created by the receptionist.
- **Order_Item**: A single line within an Order, consisting of a Menu_Item and a quantity.
- **Menu_Item**: A predefined or custom cafe product (food or drink) with a name and price.
- **Table_Number**: A numeric or short alphanumeric identifier that associates an Order with a physical table.
- **Active_Order**: An Order whose status is either `pending` or `fulfilled`.
- **Order_History**: The collection of Orders whose status is `payment_received`, scoped to the current calendar day.
- **Receptionist**: The staff user who enters and manages orders in the system.
- **Status**: The lifecycle stage of an Order — one of `pending`, `fulfilled`, or `payment_received`.

---

## Requirements

### Requirement 1: New Order Entry

**User Story:** As a receptionist, I want to enter a new cafe order with a table number and one or more menu items, so that the kitchen and service staff can see what each table has ordered.

#### Acceptance Criteria

1. THE Cafe_System SHALL provide an order entry form containing a Table_Number input field and an Order_Item list.
2. WHEN the receptionist submits the order entry form, THE Cafe_System SHALL validate that the Table_Number field is not empty.
3. WHEN the receptionist submits the order entry form, THE Cafe_System SHALL validate that at least one Order_Item has been added with a quantity greater than zero.
4. IF the Table_Number field is empty when the form is submitted, THEN THE Cafe_System SHALL display a validation error message and retain the entered form data.
5. IF no Order_Item has been added when the form is submitted, THEN THE Cafe_System SHALL display a validation error message and retain the entered form data.
6. WHEN a valid order entry form is submitted, THE Cafe_System SHALL create an Order with status `pending` and record the timestamp of creation.
7. WHEN a valid order entry form is submitted, THE Cafe_System SHALL display a success confirmation and reset the form for the next order entry.

### Requirement 2: Menu Item Selection

**User Story:** As a receptionist, I want to pick items from a predefined menu list or enter a custom item, so that I can quickly and accurately record what was ordered.

#### Acceptance Criteria

1. THE Cafe_System SHALL maintain a list of predefined Menu_Items, each with a name and a price in INR.
2. WHEN adding an Order_Item, THE Cafe_System SHALL allow the receptionist to select a Menu_Item from the predefined list.
3. WHEN adding an Order_Item, THE Cafe_System SHALL allow the receptionist to enter a custom item name not present in the predefined list.
4. WHEN a Menu_Item is selected from the predefined list, THE Cafe_System SHALL auto-populate the unit price for that Order_Item.
5. THE Cafe_System SHALL allow the receptionist to add multiple Order_Items to a single Order before submitting.
6. THE Cafe_System SHALL allow the receptionist to remove an Order_Item from the form before the Order is submitted.
7. THE Cafe_System SHALL allow administrators to add new Menu_Items to the predefined list through the Django admin interface.

### Requirement 3: Active Orders Board

**User Story:** As a receptionist, I want to see all current (non-completed) orders on a single board, so that I can monitor the status of every table at a glance.

#### Acceptance Criteria

1. THE Cafe_System SHALL display an Active Orders Board showing all Orders with status `pending` or `fulfilled`.
2. WHEN an Order is displayed on the Active Orders Board, THE Cafe_System SHALL show the Order ID, Table_Number, list of Order_Items with quantities, time placed, and current Status.
3. THE Cafe_System SHALL display Active Orders sorted by time placed in ascending order (oldest first).
4. WHEN no Active_Orders exist, THE Cafe_System SHALL display an empty-state message indicating there are no current orders.
5. WHEN an Order's status changes, THE Cafe_System SHALL reflect the updated status on the Active Orders Board without requiring a full page reload.

### Requirement 4: Order Status Management — Fulfilled

**User Story:** As a receptionist, I want to mark an order as Fulfilled when the food or drink has been delivered to the table, so that the team knows the order has been served.

#### Acceptance Criteria

1. WHEN an Order has status `pending`, THE Cafe_System SHALL display a "Mark Fulfilled" action button on that Order's card.
2. WHEN the receptionist activates the "Mark Fulfilled" action on a `pending` Order, THE Cafe_System SHALL update the Order's status to `fulfilled` and record the fulfillment timestamp.
3. WHEN an Order's status is updated to `fulfilled`, THE Cafe_System SHALL remove the "Mark Fulfilled" button and display a "Mark Payment Received" button on that Order's card.
4. IF the "Mark Fulfilled" action is requested for an Order that is not in `pending` status, THEN THE Cafe_System SHALL return an error response and leave the Order unchanged.

### Requirement 5: Order Status Management — Payment Received

**User Story:** As a receptionist, I want to mark an order as Payment Received when the table has paid, so that the order is closed and moved to history.

#### Acceptance Criteria

1. WHEN an Order has status `fulfilled`, THE Cafe_System SHALL display a "Mark Payment Received" action button on that Order's card.
2. WHEN the receptionist activates the "Mark Payment Received" action on a `fulfilled` Order, THE Cafe_System SHALL update the Order's status to `payment_received` and record the payment timestamp.
3. WHEN an Order's status is updated to `payment_received`, THE Cafe_System SHALL remove the Order from the Active Orders Board.
4. WHEN an Order's status is updated to `payment_received`, THE Cafe_System SHALL add the Order to the Order History section.
5. IF the "Mark Payment Received" action is requested for an Order that is not in `fulfilled` status, THEN THE Cafe_System SHALL return an error response and leave the Order unchanged.

### Requirement 6: Order History

**User Story:** As a receptionist, I want to view a log of all completed orders for the current day, so that I can reference what was ordered and when payments were received.

#### Acceptance Criteria

1. THE Cafe_System SHALL display an Order History section showing all Orders with status `payment_received` whose creation date matches the current calendar day.
2. WHEN an Order is displayed in Order History, THE Cafe_System SHALL show the Order ID, Table_Number, list of Order_Items with quantities, time placed, and time payment was received.
3. THE Cafe_System SHALL display Order History entries sorted by payment timestamp in descending order (most recent first).
4. WHEN no completed orders exist for the current day, THE Cafe_System SHALL display an empty-state message in the Order History section.

### Requirement 7: Navigation Integration

**User Story:** As a receptionist, I want to access the Cafe Management section from the main navigation sidebar, so that I can reach it as quickly as any other section of the system.

#### Acceptance Criteria

1. THE Cafe_System SHALL add a "Cafe" navigation link to the existing sidebar in `templates/base.html`, placed within the Main navigation section alongside Dashboard, Members, Attendance, Payments, and Inventory.
2. WHEN the current page is within the cafe section, THE Cafe_System SHALL apply the `active` CSS class to the Cafe sidebar link, consistent with the styling of other active sidebar links.
3. THE Cafe_System SHALL use the same authentication and session mechanism as the rest of the gym management system, requiring the user to be logged in to access any cafe view.

### Requirement 8: UI Consistency

**User Story:** As a receptionist, I want the Cafe Management section to look and feel like the rest of the gym management system, so that I don't have to learn a new interface.

#### Acceptance Criteria

1. THE Cafe_System SHALL use the existing `templates/base.html` as the base template for all cafe views.
2. THE Cafe_System SHALL apply the existing CSS design tokens (`--accent`, `--surface`, `--border`, `--text`, etc.) and component classes (`glass-card`, `sp-btn-primary`, `sp-btn-dark`, `dark-table`, `glow-input`, badge styles) defined in `base.html`.
3. THE Cafe_System SHALL display status badges for Order status using the existing badge style pattern: `badge-active` styling for `pending`, `badge-suspended` styling for `fulfilled`, and `badge-expired` styling for `payment_received`.
4. THE Cafe_System SHALL use the existing Django messages framework to display success and error feedback toasts, consistent with the rest of the application.
