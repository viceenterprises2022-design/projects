# Terminal Fusion — Frontend Redesign

**Date:** 2026-06-15
**Status:** Approved
**Design scope:** Complete UI/UX overhaul of all frontend HTML pages. Zero data/functionality loss.

---

## 1. Design Direction

**Terminal Fusion** — neon cyberpunk trading-desk aesthetic with animated scan-line + grid background, multi-accent color system, collapsible sidebar nav, glass panels, and JetBrains Mono typography.

---

## 2. Layout Architecture

### 2.1 Collapsible Sidebar (replaces horizontal top nav)

```
┌──────────────┬────────────────────────────────────────┐
│ ☰ AE         │  🟢 LIVE    [sym tabs]   [last-upd]   │
│ ───────────  │                                        │
│ ▸ Dashboard  │                                        │
│ ▸ Market     │          CONTENT AREA                  │
│ ▸ Portfolio  │          (dashboard, charts,           │
│ ▸ Positions  │           tables, etc.)                │
│ ▸ Holdings   │                                        │
│ ▸ Crypto     │                                        │
│ ▸ Universe   │                                        │
│ ───────────  │                                        │
│ ● LIVE       │                                        │
└──────────────┴────────────────────────────────────────┘
```

- Fixed left sidebar: 200px wide (collapsed: 56px, shows only icons)
- Hamburger icon (`☰`) at top-left toggles expand/collapse
- Logo "AE" with "AlphaEdge" text (hides text when collapsed)
- Nav links: icon + label (label hidden when collapsed)
- Active page highlighted with `--accent` color and left-border glow
- Bottom section: live status dot
- Smooth CSS transition on all sidebar animations
- Overlay on mobile, push on desktop

### 2.2 Header Bar (top)

- Thin strip above content area (not full-width like current)
- Contains: symbol tabs (NIFTY/SENSEX/BANKNIFTY), last-updated indicator, live dot
- `--accent` divider line below

---

## 3. Multi-Accent System

Each page sets `--accent` CSS variable via inline `<style>` in `<head>`.

| Page | Accent | Hex |
|------|--------|-----|
| Dashboard | Cyan | `#00f0ff` |
| Market | Emerald | `#00ff88` |
| Portfolio | Fuchsia | `#ff00ff` |
| Positions | Cyan | `#00f0ff` |
| Holdings | Emerald | `#00ff88` |
| Crypto Matrix | Fuchsia | `#ff00ff` |
| Universe | Cyan | `#00f0ff` |
| Pixi | Emerald | `#00ff88` |

**Usage:** Borders, glows, active nav indicators, accent text, button highlights, link colors.

```css
:root {
  --accent: #00f0ff;
  --accent-dim: rgba(0, 240, 255, 0.15);
  --accent-glow: 0 0 20px rgba(0, 240, 255, 0.3);
}
```

---

## 4. Background Treatment

### 4.1 Scan Lines

```css
background-image: repeating-linear-gradient(
  0deg, transparent, transparent 2px,
  rgba(255, 255, 255, 0.015) 2px, rgba(255, 255, 255, 0.015) 4px
);
```

### 4.2 Terminal Grid

```css
background-image: ... , repeating-linear-gradient(
  90deg, transparent, transparent 29px,
  rgba(255, 255, 255, 0.02) 29px, rgba(255, 255, 255, 0.02) 30px
), repeating-linear-gradient(
  0deg, transparent, transparent 29px,
  rgba(255, 255, 255, 0.02) 29px, rgba(255, 255, 255, 0.02) 30px
);
```

- Grid lines at 30px intervals, very faint (`0.02` opacity)
- Subtle pulse animation on the grid (opacity oscillation 4s cycle)
- Combined with scan lines via multiple background layers

---

## 5. Card Style (Glass Panels)

```css
.card, [class*="card"] {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--accent-dim);
  border-radius: 10px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.card:hover, [class*="card"]:hover {
  border-color: var(--accent);
  box-shadow: 0 0 25px var(--accent-glow);
}
```

---

## 6. Typography

- **Font:** JetBrains Mono (weights 400, 500, 700)
- **Fallback:** monospace
- **Loading:** `<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">`
- Remove Inter font loading (all pages)
- Monospace aligns numbers perfectly for financial data

---

## 7. Micro-interactions

| Element | Animation |
|---------|-----------|
| Page transitions | `opacity` fade (0.3s) on `<body>` via CSS transition |
| Sidebar toggle | `width` / `transform` slide (0.3s ease) |
| Nav link hover | Background highlight + accent glow intensify |
| Card hover | Border color → accent, glow box-shadow |
| LIVE dot | Scale pulse (0.5s infinite alternate) |
| Price changes | `transition: color 0.3s` (green/red) |
| Symbol tabs | Bottom border slide transition |

---

## 8. Files to Modify

| File | Changes |
|------|---------|
| `frontend/style.css` | Full rewrite: new tokens, sidebar, scan-grid bg, glass cards, JetBrains Mono, animations |
| `frontend/dashboard.html` | Collapsible sidebar nav, accent var, fade transition, JetBrains Mono font link |
| `frontend/market.html` | Same nav/accent/font changes |
| `frontend/portfolio.html` | Same |
| `frontend/positions.html` | Same |
| `frontend/holdings.html` | Same |
| `frontend/crypto_matrix.html` | Same + Fuchsia accent |
| `frontend/universe.html` | Same + remove inline nav CSS (now in style.css) |
| `frontend/pixi_dashboard.html` | Same + Emerald accent |

## 9. Non-Goals

- Not changing backend API endpoints
- Not changing data flow
- Not changing chart library (Chart.js stays)
- Not changing PixiJS logic
- Not changing any Python/JS logic

## 10. Testing

- Open each page and verify sidebar works
- Verify accent colors render per page
- Verify glass panels render with backdrop blur
- Verify scan lines + grid visible
- Verify all nav links navigate correctly
- Verify hamburger toggle works
- Verify responsive: mobile sidebar overlay
