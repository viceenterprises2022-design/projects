#!/usr/bin/env python3
"""
AlphaEdge Ticker Banner v1.0
Cross-platform Crypto PERP + NSE live ticker
Platforms: Windows | macOS | Ubuntu
Data: Hyperliquid (perpetuals) + Yahoo Finance (NSE indices & stocks)
"""

import tkinter as tk
import threading
import time
import requests
import json
import os
import platform
from datetime import datetime

# ── Optional yfinance ─────────────────────────────────────────────────────────
try:
    import yfinance as yf
    NSE_AVAILABLE = True
except ImportError:
    NSE_AVAILABLE = False

# ── File paths ────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".alphaedge_ticker.json")

# ── Default config ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "position":         "bottom",
    "height":           28,
    "scroll_speed":     1.5,
    "refresh_interval": 30,
    "font_size":        11,
    "opacity":          0.96,
    "crypto_symbols": [
        "BTC", "ETH", "SOL", "BNB", "HYPE",
        "GOLD", "SILVER", "LINK", "SUI", "PEPE"
    ],
    "nse_symbols": {
        "^NSEI":        "NIFTY 50",
        "^NSEBANK":     "BANK NIFTY",
        "RELIANCE.NS":  "RELIANCE",
        "TCS.NS":       "TCS",
        "INFY.NS":      "INFOSYS",
        "HDFCBANK.NS":  "HDFC BANK"
    },
    "show_nse":    True,
    "show_crypto": True,
}

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    "bg":      "#0d0d0f",
    "sym_cx":  "#ffd54f",
    "sym_nse": "#64b5f6",
    "price":   "#c8cdd4",
    "up":      "#00e676",
    "down":    "#ff4444",
    "sep":     "#353945",
    "border":  "#1e2028",
    "ts":      "#3a3f4b",
}

FONT = ("Consolas"        if platform.system() == "Windows" else
        "Menlo"           if platform.system() == "Darwin"  else
        "DejaVu Sans Mono")


# ── Data fetcher ──────────────────────────────────────────────────────────────
class DataFetcher:
    def __init__(self, config):
        self.config = config
        self._lock  = threading.Lock()
        self.items  = []
        self.ts     = None

    # -- Crypto --
    def fetch_crypto(self):
        try:
            resp = requests.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "metaAndAssetCtxs"},
                timeout=8
            )
            resp.raise_for_status()
            meta, ctxs = resp.json()
            wanted = set(self.config["crypto_symbols"])
            order  = {s: i for i, s in enumerate(self.config["crypto_symbols"])}
            out    = []
            for asset, ctx in zip(meta["universe"], ctxs):
                name = asset["name"]
                if name not in wanted:
                    continue
                try:
                    mark = float(ctx["markPx"])
                    prev = float(ctx["prevDayPx"])
                    pct  = (mark - prev) / prev * 100 if prev else 0.0
                    fund = float(ctx.get("funding", 0)) * 100
                    out.append({
                        "kind":    "PERP",
                        "label":   f"{name}-USD-PERP",
                        "price":   mark,
                        "change":  pct,
                        "funding": fund,
                    })
                except Exception:
                    continue
            out.sort(key=lambda x: order.get(x["label"].split("-")[0], 99))
            return out
        except Exception:
            return []

    # -- NSE --
    def fetch_nse(self):
        if not NSE_AVAILABLE or not self.config.get("show_nse", True):
            return []
        try:
            sym_map = self.config["nse_symbols"]
            syms    = list(sym_map.keys())
            raw     = yf.download(syms, period="2d", progress=False, auto_adjust=True)
            close   = raw["Close"]
            out     = []
            for sym, label in sym_map.items():
                try:
                    col  = close[sym].dropna()
                    if len(col) < 2:
                        continue
                    curr = float(col.iloc[-1])
                    prev = float(col.iloc[-2])
                    pct  = (curr - prev) / prev * 100 if prev else 0.0
                    out.append({
                        "kind":   "NSE",
                        "label":  label,
                        "price":  curr,
                        "change": pct,
                    })
                except Exception:
                    continue
            return out
        except Exception:
            return []

    def refresh(self):
        cx  = self.fetch_crypto() if self.config.get("show_crypto", True) else []
        nse = self.fetch_nse()
        with self._lock:
            self.items = cx + nse
            self.ts    = datetime.now()

    def get(self):
        with self._lock:
            return list(self.items), self.ts


# ── Banner window ─────────────────────────────────────────────────────────────
class TickerBanner:
    def __init__(self):
        self.cfg     = self._load_cfg()
        self.fetcher = DataFetcher(self.cfg)

        self.root = tk.Tk()
        self.root.title("AlphaEdge Ticker")

        self._setup_window()
        self._build_ui()

        self._segments: list = []   # (canvas_id, virtual_init_x, width)
        self._offset   = 0          # total pixels scrolled
        self._screen_w = self.root.winfo_screenwidth()
        self._content_w = 0
        self._after_id  = None
        self._dx = self._dy = 0

        self._set_loading()
        threading.Thread(target=self._initial_fetch, daemon=True).start()
        self._schedule_refresh()
        self.root.mainloop()

    # ── Config ────────────────────────────────────────────────────────────────
    def _load_cfg(self):
        if os.path.exists(CONFIG_FILE):
            try:
                saved  = json.load(open(CONFIG_FILE))
                merged = {**DEFAULT_CONFIG, **saved}
                merged["nse_symbols"]    = saved.get("nse_symbols",    DEFAULT_CONFIG["nse_symbols"])
                merged["crypto_symbols"] = saved.get("crypto_symbols", DEFAULT_CONFIG["crypto_symbols"])
                return merged
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def _save_cfg(self):
        try:
            json.dump(self.cfg, open(CONFIG_FILE, "w"), indent=2)
        except Exception:
            pass

    # ── Window ────────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=C["bg"])
        try:
            self.root.attributes("-alpha", self.cfg["opacity"])
        except Exception:
            pass
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        h  = self.cfg["height"]
        y  = 0 if self.cfg["position"] == "top" else sh - h - 1
        self.root.geometry(f"{sw}x{h}+0+{y}")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        h = self.cfg["height"]

        self._badge = tk.Label(
            self.root, text=" ◈ ALPHAEDGE ",
            bg="#0a1628", fg="#ffd54f",
            font=(FONT, 9, "bold"), padx=0, pady=0, bd=0
        )
        self._badge.pack(side="left", fill="y")
        self._badge.bind("<Button-3>", self._show_menu)
        self._badge.bind("<Button-1>", self._drag_start)
        self._badge.bind("<B1-Motion>", self._drag_do)

        self._cv = tk.Canvas(
            self.root, height=h,
            bg=C["bg"], highlightthickness=0, bd=0
        )
        self._cv.pack(side="left", fill="x", expand=True)
        self._cv.bind("<Configure>",   self._on_resize)
        self._cv.bind("<Button-1>",    self._drag_start)
        self._cv.bind("<B1-Motion>",   self._drag_do)
        self._cv.bind("<Button-3>",    self._show_menu)

        # Top highlight line
        self._cv.create_line(0, 0, 9999, 0, fill=C["border"], width=1, tags="border")
        # Bottom highlight
        self._cv.create_line(0, h-1, 9999, h-1, fill=C["border"], width=1, tags="border")

        self._ts_lbl = tk.Label(
            self.root, text=" ─── ",
            bg=C["bg"], fg=C["ts"],
            font=(FONT, 8), padx=4, pady=0
        )
        self._ts_lbl.pack(side="right", fill="y")
        self._ts_lbl.bind("<Button-3>", self._show_menu)

        self.root.bind("<Escape>", lambda e: self._quit())

    def _on_resize(self, event):
        self._screen_w = event.width

    # ── Loading ───────────────────────────────────────────────────────────────
    def _set_loading(self):
        h = self.cfg["height"]
        self._cv.delete("ticker")
        self._cv.create_text(
            120, h // 2 + 1,
            text="⟳  Connecting to Hyperliquid & NSE…",
            fill=C["ts"], font=(FONT, self.cfg["font_size"]),
            anchor="w", tags="ticker"
        )

    def _initial_fetch(self):
        self.fetcher.refresh()
        self.root.after(0, self._rebuild)

    # ── Rebuild ticker ────────────────────────────────────────────────────────
    def _rebuild(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        self._cv.delete("ticker")
        self._segments = []

        items, ts = self.fetcher.get()

        if ts:
            self._ts_lbl.config(text=ts.strftime(" %H:%M:%S "), fg=C["ts"])

        if not items:
            self._cv.create_text(
                120, self.cfg["height"] // 2 + 1,
                text="⚠  No data — right-click → Refresh",
                fill=C["down"], font=(FONT, self.cfg["font_size"]),
                anchor="w", tags="ticker"
            )
            return

        h  = self.cfg["height"]
        fs = self.cfg["font_size"]
        cy = h // 2 + 1
        sw = self._screen_w or self.root.winfo_screenwidth()

        segs = []
        for item in items:
            chg   = item["change"]
            c_chg = C["up"] if chg >= 0 else C["down"]
            arrow = "▲" if chg >= 0 else "▼"
            c_sym = C["sym_cx"] if item["kind"] == "PERP" else C["sym_nse"]

            segs.append((f"  {item['label']}  ", c_sym,  (FONT, fs, "bold")))
            segs.append((self._fmt(item["price"], item["kind"]),
                         C["price"],              (FONT, fs)))
            segs.append((f"  {arrow}{abs(chg):.2f}%",
                         c_chg,                   (FONT, fs, "bold")))
            if item["kind"] == "PERP" and abs(item.get("funding", 0)) >= 0.001:
                fr  = item["funding"]
                crf = C["up"] if fr >= 0 else C["down"]
                segs.append((f"  ƒ{fr:+.4f}%", crf, (FONT, fs - 1)))
            segs.append(("   ◆   ", C["sep"], (FONT, fs - 2)))

        cursor_x = sw
        for text, fill, fnt in segs:
            tid = self._cv.create_text(
                cursor_x, cy,
                text=text, fill=fill, font=fnt,
                anchor="w", tags="ticker"
            )
            bbox = self._cv.bbox(tid)
            w = (bbox[2] - bbox[0]) if bbox else max(len(text) * (fs - 1), 1)
            self._segments.append([tid, cursor_x, w])
            cursor_x += w

        self._content_w = max(cursor_x - sw, 1)
        self._offset    = 0
        self._scroll_loop()

    # ── Scroll loop (~60fps) ──────────────────────────────────────────────────
    def _scroll_loop(self):
        speed = self.cfg["scroll_speed"]
        sw    = self._screen_w or self.root.winfo_screenwidth()
        self._offset += speed

        for seg in self._segments:
            tid, init_x, w = seg
            vx = init_x - self._offset
            # Wrap around: when right edge of item goes off left edge
            if vx + w < 0:
                seg[1] += self._content_w + sw  # bump init_x forward one loop
                vx = seg[1] - self._offset
            # Move text to computed position
            cur_coords = self._cv.coords(tid)
            if cur_coords:
                self._cv.coords(tid, vx, cur_coords[1])

        self._after_id = self.root.after(16, self._scroll_loop)

    # ── Format ───────────────────────────────────────────────────────────────
    def _fmt(self, price, kind):
        if kind == "NSE":
            return f"{price:,.2f}" if price < 10000 else f"{price:,.0f}"
        if price >= 10000: return f"${price:,.0f}"
        if price >= 1:     return f"${price:.3f}"
        return f"${price:.5f}"

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_do(self, e):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        h  = self.cfg["height"]
        ny = max(0, min(sh - h, e.y_root - self._dy))
        self.root.geometry(f"{sw}x{h}+0+{ny}")
        self.cfg["position"] = "top" if ny < sh // 2 else "bottom"

    # ── Right-click menu ──────────────────────────────────────────────────────
    def _show_menu(self, e):
        m = tk.Menu(self.root, tearoff=0,
                    bg="#141620", fg="#c8cdd4",
                    activebackground="#252838", activeforeground="#ffffff",
                    font=(FONT, 10))
        m.add_command(label="⟳   Refresh Now",     command=self._manual_refresh)
        m.add_separator()
        pos = "Bottom" if self.cfg["position"] == "top" else "Top"
        m.add_command(label=f"↕   Move to {pos}",   command=self._toggle_pos)
        m.add_separator()
        m.add_command(
            label=("Hide NSE"    if self.cfg["show_nse"]    else "Show NSE"),
            command=self._toggle_nse
        )
        m.add_command(
            label=("Hide Crypto" if self.cfg["show_crypto"] else "Show Crypto"),
            command=self._toggle_crypto
        )
        m.add_separator()

        sm = tk.Menu(m, tearoff=0, bg="#141620", fg="#c8cdd4",
                     activebackground="#252838", activeforeground="#ffffff",
                     font=(FONT, 10))
        for spd, lbl in [(0.8,"Slow"), (1.5,"Normal"), (2.5,"Fast"), (4.0,"Turbo")]:
            dot = "●" if abs(spd - self.cfg["scroll_speed"]) < 0.4 else "○"
            sm.add_command(label=f"{dot}  {lbl}", command=lambda s=spd: self._set_speed(s))
        m.add_cascade(label="⚡  Scroll Speed",     menu=sm)

        om = tk.Menu(m, tearoff=0, bg="#141620", fg="#c8cdd4",
                     activebackground="#252838", activeforeground="#ffffff",
                     font=(FONT, 10))
        for op, lbl in [(0.6,"60%"),(0.8,"80%"),(0.96,"96%"),(1.0,"100%")]:
            dot = "●" if abs(op - self.cfg["opacity"]) < 0.05 else "○"
            om.add_command(label=f"{dot}  {lbl}", command=lambda o=op: self._set_opacity(o))
        m.add_cascade(label="◐   Opacity",          menu=om)
        m.add_separator()
        m.add_command(label="✕   Quit",              command=self._quit)
        m.post(e.x_root, e.y_root)

    def _manual_refresh(self):
        def _bg():
            self.fetcher.refresh()
            self.root.after(0, self._rebuild)
        threading.Thread(target=_bg, daemon=True).start()

    def _toggle_pos(self):
        sw, sh, h = (self.root.winfo_screenwidth(),
                     self.root.winfo_screenheight(), self.cfg["height"])
        if self.cfg["position"] == "top":
            self.cfg["position"] = "bottom"
            self.root.geometry(f"{sw}x{h}+0+{sh-h-1}")
        else:
            self.cfg["position"] = "top"
            self.root.geometry(f"{sw}x{h}+0+0")
        self._save_cfg()

    def _toggle_nse(self):
        self.cfg["show_nse"] = not self.cfg["show_nse"]
        self._save_cfg(); self._manual_refresh()

    def _toggle_crypto(self):
        self.cfg["show_crypto"] = not self.cfg["show_crypto"]
        self._save_cfg(); self._manual_refresh()

    def _set_speed(self, s):
        self.cfg["scroll_speed"] = s; self._save_cfg()

    def _set_opacity(self, o):
        self.cfg["opacity"] = o
        self._save_cfg()
        try: self.root.attributes("-alpha", o)
        except Exception: pass

    def _schedule_refresh(self):
        self.root.after(self.cfg["refresh_interval"] * 1000, self._bg_refresh)

    def _bg_refresh(self):
        threading.Thread(target=lambda: (
            self.fetcher.refresh(),
            self.root.after(0, self._rebuild)
        ), daemon=True).start()
        self._schedule_refresh()

    def _quit(self):
        self._save_cfg()
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self.root.destroy()


# ── README text ───────────────────────────────────────────────────────────────
README = """
# AlphaEdge Ticker Banner — README

## Requirements
  Python 3.8+   (built-in tkinter)
  pip install requests yfinance

## Run
  python alphaedge_ticker.py

## Controls
  Drag           — move bar up/down screen (snaps to full width)
  Right-click    — context menu
                     ⟳ Refresh Now
                     ↕ Move to Top/Bottom
                     📈 Show/Hide NSE
                     ₿  Show/Hide Crypto
                     ⚡ Scroll Speed (Slow / Normal / Fast / Turbo)
                     ◐  Opacity (60% – 100%)
                     ✕  Quit
  Esc            — Quit

## Data Sources
  Crypto : Hyperliquid public API (no key needed)
           Shows PERP mark price, 24h change %, funding rate
  NSE    : Yahoo Finance via yfinance
           NIFTY 50, BANK NIFTY, RELIANCE, TCS, INFOSYS, HDFC BANK

## Config file (~/.alphaedge_ticker.json)
  Edit to add/remove symbols, change refresh interval, etc.
  Example — add more NSE stocks:
    "nse_symbols": {
      "^NSEI":       "NIFTY 50",
      "WIPRO.NS":    "WIPRO",
      "TATAMOTORS.NS": "TATA MOTORS"
    }
  Add more crypto perps (must be listed on Hyperliquid):
    "crypto_symbols": ["BTC","ETH","SOL","HYPE","WIF","BONK"]

## Platform notes
  Windows : Works natively. Add to Task Scheduler for auto-start.
  macOS   : Works natively. Grant "Accessibility" in System Prefs if needed.
  Ubuntu  : Requires python3-tk  →  sudo apt install python3-tk
            For auto-start: add to ~/.config/autostart/
"""


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AlphaEdge Ticker Banner v1.0")
    print("  Crypto PERP (Hyperliquid) + NSE (Yahoo Finance)")
    print("=" * 60)
    print(f"  Platform  : {platform.system()} {platform.release()}")
    print(f"  Config    : {CONFIG_FILE}")
    print(f"  NSE Data  : {'yfinance OK' if NSE_AVAILABLE else 'yfinance missing — pip install yfinance'}")
    print()
    print("  Right-click for options  |  Esc to quit")
    print("=" * 60)
    TickerBanner()
