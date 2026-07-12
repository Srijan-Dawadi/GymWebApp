---
inclusion: always
---

# 5 Star Fitness — Design System & Theme Guide

This document defines the visual identity, design tokens, and component standards for the 5 Star Fitness gym management system. All UI work must follow these guidelines.

## Brand Identity

**Name**: 5 Star Fitness  
**Personality**: Premium, powerful, disciplined — like a high-end gym, not a generic SaaS tool  
**Visual Direction**: Dark, high-contrast, with a bold amber/gold accent that signals energy and achievement. Think less "Spotify clone", more "elite performance dashboard".

---

## Color Tokens

### Primitive Palette

```css
/* Amber/Gold — primary brand accent */
--amber-300: #fcd34d;
--amber-400: #fbbf24;
--amber-500: #f59e0b;   /* Base accent */
--amber-600: #d97706;
--amber-700: #b45309;

/* Neutral Dark Scale */
--neutral-950: #0a0a0a;  /* Deepest bg */
--neutral-900: #111111;  /* Page bg */
--neutral-850: #161616;  /* Sidebar bg */
--neutral-800: #1c1c1c;  /* Card bg */
--neutral-750: #222222;  /* Card hover / elevated surface */
--neutral-700: #2a2a2a;  /* Input bg */
--neutral-600: #333333;  /* Border */
--neutral-500: #444444;  /* Border strong */
--neutral-400: #666666;  /* Border light / muted icon */
--neutral-300: #888888;  /* Text muted */
--neutral-200: #aaaaaa;  /* Text secondary */
--neutral-100: #cccccc;  /* Text body */
--neutral-50:  #eeeeee;  /* Text primary (not pure white) */
--white:       #ffffff;  /* Headings, labels */

/* Semantic Status */
--green-500:  #22c55e;   /* Success / active */
--green-400:  #4ade80;
--red-500:    #ef4444;   /* Error / danger */
--red-400:    #f87171;
--orange-500: #f97316;   /* Warning */
--orange-400: #fb923c;
--blue-500:   #3b82f6;   /* Info */
--blue-400:   #60a5fa;
```

### Semantic Token Mapping

```css
:root {
  /* Backgrounds */
  --bg-page:       var(--neutral-900);
  --bg-sidebar:    var(--neutral-850);
  --bg-card:       var(--neutral-800);
  --bg-card-hover: var(--neutral-750);
  --bg-input:      var(--neutral-700);
  --bg-elevated:   var(--neutral-750);

  /* Borders */
  --border:        var(--neutral-600);
  --border-strong: var(--neutral-500);
  --border-subtle: #1e1e1e;

  /* Text */
  --text-primary:   var(--white);
  --text-body:      var(--neutral-100);
  --text-secondary: var(--neutral-200);
  --text-muted:     var(--neutral-300);
  --text-disabled:  var(--neutral-400);

  /* Brand Accent */
  --accent:         var(--amber-500);
  --accent-hover:   var(--amber-400);
  --accent-dim:     rgba(245, 158, 11, 0.12);
  --accent-border:  rgba(245, 158, 11, 0.3);

  /* Status */
  --success:        var(--green-500);
  --success-dim:    rgba(34, 197, 94, 0.12);
  --success-border: rgba(34, 197, 94, 0.3);

  --danger:         var(--red-500);
  --danger-dim:     rgba(239, 68, 68, 0.12);
  --danger-border:  rgba(239, 68, 68, 0.3);

  --warning:        var(--orange-500);
  --warning-dim:    rgba(249, 115, 22, 0.12);
  --warning-border: rgba(249, 115, 22, 0.3);

  --info:           var(--blue-500);
  --info-dim:       rgba(59, 130, 246, 0.12);
  --info-border:    rgba(59, 130, 246, 0.3);
}
```

---

## Typography

**Font Stack**: `'Inter', 'Helvetica Neue', Arial, sans-serif`  
Use Inter from Google Fonts. It is more professional and legible than CircularSp.

### Scale

| Token | Size | Use |
|---|---|---|
| `--text-xs` | 11px / 0.6875rem | Labels, overlines, badges |
| `--text-sm` | 13px / 0.8125rem | Table cells, secondary info |
| `--text-base` | 14px / 0.875rem | Body, nav links, buttons |
| `--text-md` | 15px / 0.9375rem | Card values, list items |
| `--text-lg` | 18px / 1.125rem | Section headings |
| `--text-xl` | 22px / 1.375rem | Page headings |
| `--text-2xl` | 28px / 1.75rem | Stat numbers |
| `--text-3xl` | 36px / 2.25rem | Hero numbers |

### Rules
- Headings: `font-weight: 700`, `color: var(--text-primary)`
- Body: `font-weight: 400`, `color: var(--text-body)`
- Labels/overlines: `font-weight: 600`, `text-transform: uppercase`, `letter-spacing: 0.08em`, `color: var(--text-muted)`
- Stat numbers: `font-weight: 800`, `font-variant-numeric: tabular-nums`
- **Never use `letter-spacing: 1.4px` on body text** — only on uppercase labels

---

## Spacing

Base unit: **4px**. Use multiples of 4.

| Token | Value | Use |
|---|---|---|
| `--space-1` | 4px | Tight gaps (icon + label) |
| `--space-2` | 8px | Inner padding small |
| `--space-3` | 12px | Badge padding, tight rows |
| `--space-4` | 16px | Default padding, row height |
| `--space-5` | 20px | Card padding |
| `--space-6` | 24px | Section gaps |
| `--space-8` | 32px | Large section gaps |
| `--space-10` | 40px | Page-level padding |

---

## Border Radius

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 4px | Table rows, small chips |
| `--radius-md` | 8px | Cards, modals, dropdowns |
| `--radius-lg` | 12px | Large cards, panels |
| `--radius-xl` | 16px | Login card |
| `--radius-full` | 9999px | Buttons, badges, pills, inputs |

**Rule**: Inputs and buttons use `--radius-full`. Cards use `--radius-md`. Modals use `--radius-lg`.

---

## Component Standards

### Buttons

```css
/* Primary — amber, black text */
.btn-primary {
  background: var(--accent);
  color: #000;
  border-radius: var(--radius-full);
  padding: 9px 24px;
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: none;
  transition: background 0.15s, transform 0.1s;
}
.btn-primary:hover { background: var(--accent-hover); transform: scale(1.02); }

/* Secondary — dark surface */
.btn-secondary {
  background: var(--bg-elevated);
  color: var(--text-body);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  padding: 9px 20px;
  font-size: var(--text-base);
  font-weight: 600;
}
.btn-secondary:hover { border-color: var(--border-strong); background: #303030; }

/* Danger */
.btn-danger {
  background: var(--danger-dim);
  color: var(--danger);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-full);
  padding: 9px 20px;
  font-size: var(--text-base);
  font-weight: 600;
}
```

### Inputs

```css
.input {
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  padding: 10px 16px;
  font-size: var(--text-base);
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
  width: 100%;
}
.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-dim);
}
.input::placeholder { color: var(--text-disabled); }
/* Textarea and select: use --radius-md instead */
```

### Cards

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
.card:hover { border-color: var(--border); }
```

### Status Badges

```css
.badge { border-radius: var(--radius-full); padding: 3px 10px; font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; display: inline-block; }
.badge-active    { background: var(--success-dim); color: var(--success); border: 1px solid var(--success-border); }
.badge-expired   { background: var(--danger-dim);  color: var(--danger);  border: 1px solid var(--danger-border); }
.badge-suspended { background: var(--warning-dim); color: var(--warning); border: 1px solid var(--warning-border); }
```

### Tables

```css
.table thead { background: var(--bg-elevated); border-bottom: 1px solid var(--border); }
.table th { color: var(--text-muted); font-size: var(--text-xs); font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; padding: 12px 16px; }
.table td { padding: 13px 16px; border-bottom: 1px solid var(--border-subtle); color: var(--text-body); font-size: var(--text-sm); }
.table tbody tr:hover td { background: var(--bg-card-hover); color: var(--text-primary); }
```

### Sidebar

- Background: `var(--bg-sidebar)` with a right border `1px solid var(--border-subtle)`
- Active link: left border `3px solid var(--accent)`, text `var(--text-primary)`, weight 700
- Inactive link: text `var(--text-secondary)`, hover `var(--text-primary)`
- Section labels: `var(--text-muted)`, uppercase, `var(--text-xs)`
- Logo accent: `var(--accent)` background, black text

---

## Accent Color Rationale

The original Spotify green (`#1ed760`) was replaced with **amber/gold** (`#f59e0b`) because:
- Green is strongly associated with Spotify — using it makes the app feel like a Spotify clone
- Amber/gold communicates **achievement, energy, and premium quality** — appropriate for a fitness brand
- Gold is used by premium fitness brands (Gold's Gym, etc.) and signals excellence
- It provides strong contrast on dark backgrounds (WCAG AA compliant: 4.6:1 on `#111111`)

---

## What to Avoid

- ❌ Pure black (`#000000`) backgrounds — use `#111111` or `#0a0a0a`
- ❌ Pure white (`#ffffff`) for body text — use `#cccccc` or `#eeeeee`
- ❌ Hardcoded hex values in templates — always reference CSS variables
- ❌ `letter-spacing: 1.4px` on non-uppercase text
- ❌ Mixing border-radius styles (e.g., pill buttons next to square cards)
- ❌ Inline `onmouseover` style hacks — use CSS classes with `:hover`
- ❌ Spotify green (`#1ed760`) — this is not a Spotify product

---

## Chart Colors

For Chart.js and data visualizations:
- Primary data: `rgba(245, 158, 11, 0.7)` fill, `#f59e0b` border
- Secondary data: `rgba(59, 130, 246, 0.6)` fill, `#3b82f6` border
- Success/positive: `rgba(34, 197, 94, 0.6)` fill, `#22c55e` border
- Grid lines: `rgba(255, 255, 255, 0.05)`
- Tick labels: `#666666`
- Tooltip bg: `#1c1c1c`, border: `#333333`

---

## Sidebar Logo

The logo mark should be a bold **"5★"** or a dumbbell icon on an amber background square with rounded corners (`--radius-md`). Not a circle. Not an emoji.

---

## Page Structure

```
body (bg-page)
  └── sidebar (bg-sidebar, fixed width 256px)
  └── main area
        └── top header (bg-page, sticky, border-bottom)
        └── content (padding 24px)
```

Content max-width: none (full width within the main area). Cards use internal padding of `var(--space-5)` (20px).
