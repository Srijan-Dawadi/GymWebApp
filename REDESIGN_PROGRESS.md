# Spotify Design System Redesign Progress

## ✅ Completed

### 1. Fixed Dependencies
- Updated `onnxruntime==1.21.0` → `onnxruntime==1.24.1` (version 1.21.0 doesn't exist)
- Added back `gunicorn==22.0.0` and `psycopg2-binary==2.9.11` for production

### 2. Base Template (templates/base.html)
**Complete Spotify redesign applied:**

#### Color System
- Background: `#121212` (near-black immersive)
- Surface: `#181818` (cards, sidebar)
- Accent: `#1ed760` (Spotify Green - functional only)
- Text: `#ffffff`, `#cbcbcb`, `#b3b3b3` (hierarchy)
- Semantic: `#f3727f` (error), `#ffa42b` (warning), `#539df5` (info)

#### Typography
- Font: CircularSp with extensive fallbacks
- Weights: 700 (bold) / 400 (regular) binary
- Button labels: UPPERCASE with 1.4px letter-spacing
- Compact sizing: 10px–24px range

#### Components
- **Buttons**: Full pill shape (9999px radius), uppercase labels
  - Primary: Spotify Green with black text
  - Dark: `#1f1f1f` background
  - Outlined: transparent with border
- **Inputs**: 500px pill radius, inset shadow border
- **Cards**: 8px radius, `#181818` background
- **Sidebar**: Near-black with left-border active state
- **Status Badges**: Pill-shaped with semantic colors
- **Modals**: Dark with heavy shadows
- **Toasts**: Pill-shaped with semantic colors

#### Interactions
- Hover: subtle color transitions (no lift/glow)
- Focus: white inset border on inputs
- Active nav: left border + bold weight
- Custom select dropdowns: dark themed

## 📋 Next Steps

### Templates to Redesign (in order):

1. **templates/accounts/login.html** - Login page
2. **templates/accounts/dashboard.html** - Main dashboard
3. **templates/members/list.html** - Members list
4. **templates/members/detail.html** - Member detail
5. **templates/members/form.html** - Member form
6. **templates/attendance/attendance.html** - Attendance page
7. **templates/billing/payments.html** - Payments list
8. **templates/billing/plans.html** - Plans management
9. **templates/billing/payment_form.html** - Payment form
10. **templates/billing/plan_form.html** - Plan form
11. **templates/accounts/reports.html** - Reports page
12. **templates/accounts/users.html** - User management
13. **templates/accounts/user_form.html** - User form
14. **templates/Inventory/inventory.html** - Inventory page

### Design Principles to Apply

From DESIGN.md:

**Do:**
- Use near-black backgrounds (`#121212`–`#1f1f1f`)
- Apply Spotify Green only for play controls, active states, CTAs
- Use pill shape (500px–9999px) for all buttons
- Apply uppercase + wide letter-spacing on button labels
- Keep typography compact (10px–24px)
- Use heavy shadows (0.3–0.5 opacity) for elevation
- Let content provide color — UI is achromatic

**Don't:**
- Use Spotify Green decoratively
- Use light backgrounds for primary surfaces
- Skip pill/circle geometry on buttons
- Use thin/subtle shadows
- Add additional brand colors
- Use relaxed line-heights
- Expose raw gray borders

## Installation Instructions

```bash
# Install dependencies (fixed version)
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py create_superuser

# Run development server
python manage.py runserver
```

## Design System Reference

See `DESIGN.md` for complete Spotify design system documentation including:
- Visual theme & atmosphere
- Color palette & roles
- Typography rules
- Component stylings
- Layout principles
- Depth & elevation
- Responsive behavior
