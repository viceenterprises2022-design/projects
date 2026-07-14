# AlphaEdge UI/UX Design System

A developer-first, premium minimalist dark aesthetic designed for automated retail and professional traders.

## Color Palette

| Token | Hex | Role |
|---|---|---|
| `--bg-primary` | `#080c14` | Main page background |
| `--bg-secondary` | `#0e1524` | Card/panel backgrounds |
| `--bg-tertiary` | `#172033` | Dropdown/hover item backgrounds |
| `--border-subtle` | `#1f2b45` | Structural element borders |
| `--text-primary` | `#f1f5f9` | High-contrast readability text |
| `--text-secondary` | `#94a3b8` | Supporting metadata/labels |
| `--text-muted` | `#64748b` | Disabled states/subtle timestamps |
| `--accent-gold` | `#fbbf24` | Main brand color, active highlights |
| `--accent-purple` | `#c084fc` | Signal plane / data factors indicator |
| `--status-success` | `#34d399` | Live mode / order filled / ledger verified |
| `--status-danger` | `#f87171` | Paused / kill-switched / risk breach |

## Typography

- **Primary Font**: `Inter`, system-ui, sans-serif
- **Code Font**: `JetBrains Mono`, monospace (for ledger hashes and raw signals)
- **Weights**:
  - `Regular`: 400
  - `Medium`: 500
  - `Semibold`: 600
  - `Bold`: 700

## Spacing & Layout

- **Border Radius**:
  - Card/Panels: `8px` (`0.5rem`)
  - Buttons/Inputs: `6px` (`0.375rem`)
- **Spacing Scale**:
  - Small: `8px`
  - Medium: `16px`
  - Large: `24px`
  - Extra Large: `32px`

## Key Micro-Animations & Effects

1. **Card Hover**: Translate Y by `-2px`, transition border color and box-shadow smoothly over `200ms ease-out`.
2. **Glassmorphism**: Combine `backdrop-filter: blur(12px)` with low-opacity borders for header components.
3. **Pulse indicator**: Soft repeating glow for active trade connections.
