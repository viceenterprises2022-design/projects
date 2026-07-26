'use client';

import { useEffect, useState } from 'react';

// Theme switch. Dark is the product's default and the value it falls back to;
// light is opt-in and remembered in localStorage. The <html data-theme> stamp
// is applied by an inline script in the layout BEFORE first paint, so there is
// no flash — this component only reflects and updates it.

export type Theme = 'dark' | 'light';

export default function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const [theme, setTheme] = useState<Theme>('dark');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const current = (document.documentElement.getAttribute('data-theme') as Theme) || 'dark';
    setTheme(current);
    setMounted(true);
  }, []);

  const toggle = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('prospera-theme', next); } catch { /* private mode */ }
    setTheme(next);
  };

  const isDark = theme === 'dark';
  // Render the dark-state icon until mounted so server and client markup agree.
  const showDark = mounted ? isDark : true;

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={showDark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={showDark ? 'Light mode' : 'Dark mode'}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: compact ? 28 : 34, height: compact ? 28 : 34,
        borderRadius: 999, cursor: 'pointer', flexShrink: 0,
        // Colours are derived from state, NOT CSS variables. The control that
        // switches the theme must never depend on theme CSS resolving
        // correctly — when it did, a stale cascade left it invisible against
        // the very background it was sitting on.
        background: showDark ? 'rgba(255,255,255,0.06)' : 'rgba(11,18,32,0.06)',
        border: `1px solid ${showDark ? 'rgba(255,255,255,0.22)' : 'rgba(11,18,32,0.24)'}`,
        color: showDark ? '#f4f7ff' : '#0b1220',
        transition: 'background 180ms ease, border-color 180ms ease, color 180ms ease',
        padding: 0,
      }}
    >
      <svg width={compact ? 13 : 15} height={compact ? 13 : 15} viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {showDark ? (
          // moon — currently dark, click for light
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        ) : (
          // sun — currently light, click for dark
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
          </>
        )}
      </svg>
    </button>
  );
}
