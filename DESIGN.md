# DESIGN.md - AI Design System Brief

This document serves as the visual identity source of truth for AI coding agents.

## 1. Visual Theme & Atmosphere
- **Aesthetic:** Minimalist, high-contrast, "Developer-first" interface. 
- **Core Vibes:** Clean, functional, data-dense but readable, monochrome with vibrant accents.

## 2. Color Palette & Roles
- **Background (Surface):** `#000000` (Pitch Black)
- **Primary (Action):** `#10B981` (Emerald Green)
- **Secondary (Accents):** `#3B82F6` (Blue)
- **Text (Primary):** `#FFFFFF` (Pure White)
- **Text (Secondary/Muted):** `#94A3B8` (Slate 400)
- **Border:** `#1E293B` (Slate 800)
- **Error:** `#EF4444` (Red)

## 3. Typography Rules
- **Font Family:** `Inter`, system-ui, sans-serif.
- **Weights:** Regular (400), Medium (510), Bold (700).
- **Scale:** 
  - H1: 2rem / 32px
  - H2: 1.5rem / 24px
  - Base: 1rem / 16px
  - Small: 0.875rem / 14px

## 4. Component Styles
- **Buttons:** 
  - Radius: 6px
  - Border: 1px solid transparent
  - Padding: 8px 16px
- **Inputs:**
  - Background: `#0F172A` (Slate 900)
  - Border: 1px solid `#1E293B`
- **Cards:**
  - Border: 1px solid `#1E293B`
  - Radius: 8px

## 5. Layout Principles
- **Grid:** 12-column system.
- **Spacing Scale:** 4px (base), 8px, 16px, 24px, 32px, 64px.
- **Container:** Max-width 1280px.

## 6. Depth & Elevation
- **Elevation 1:** `box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)`
- **Layering:** Background `#000000` -> Surface `#0F172A` -> Component `#1E293B`.

## 7. Design Don'ts (Anti-patterns)
- NO full-uppercase text in UI elements.
- NO gradients unless specifically for data visualization.
- NO rounded corners larger than 8px.
- NO shadows on dark background elements.

## 8. Responsive Rules
- **Mobile (< 640px):** Single column, full-width components.
- **Tablet (640px - 1024px):** 2-column grids for cards.
- **Desktop (> 1024px):** Standard multi-column layouts.

## 9. AI Agent Prompt Guide
- Always use the hex codes defined in Section 2 for CSS variables or Tailwind config.
- Prefer Vanilla CSS or Tailwind CSS for implementation.
- Maintain strict alignment to the 4px spacing scale.
- Use `Inter` weight 510 for primary text to ensure crispness on dark backgrounds.
