#!/usr/bin/env python3
"""
AlphaEdge Ticker v2.0 — NSE/BSE Indices · Options via Upstox
"""
import tkinter as tk
import threading
import requests
import json
import os
import platform
from datetime import datetime, date, timedelta

# ── Paths ─────────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".alphaedge_ticker.json")

# ── Default config ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "upstox_token": "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9.lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo",               # paste token here or in ~/.alphaedge_ticker.json
    "position":         "bottom",
    "height":           28,
    "scroll_speed":     3.0,
    "refresh_interval": 30,
    "font_size":        11,
    "opacity":          0.96,
    "indices": {
        "NSE_INDEX|Nifty 50":           "NIFTY",
        "NSE_INDEX|Nifty Bank":         "BANKNIFTY",
        "BSE_INDEX|SENSEX":             "SENSEX",
        "NSE_INDEX|Nifty Fin Service":  "FINNIFTY",
        "NSE_INDEX|NIFTY MIDCAP 100":  "MIDCAP",
    },
    # expiry auto-detected from API — no manual weekday config needed
    "option_chains": {
        "NSE_INDEX|Nifty 50":   {"label": "NIFTY",  "step": 50,  "strikes_around": 2},
        "NSE_INDEX|Nifty Bank": {"label": "BNKN",   "step": 100, "strikes_around": 2},
        "BSE_INDEX|SENSEX":     {"label": "SENSEX", "step": 100, "strikes_around": 2},
    },
    "show_indices": True,
    "show_options": True,
}

# ── Colours ───────────────────────────────────────────────────────────────────
C = {
    "bg":     "#0d0d0f",
    "idx":    "#ffd54f",   # indices label  — gold
    "ce":     "#a5d6a7",   # call options   — muted green
    "pe":     "#ef9a9a",   # put options    — muted rose
    "ce_atm": "#69f0ae",   # ATM call       — bright green
    "pe_atm": "#ff5252",   # ATM put        — bright red
    "price":  "#c8cdd4",
    "up":     "#00e676",
    "down":   "#ff4444",
    "meta":   "#8a8f9a",   # OI / IV labels
    "sep":    "#353945",
    "border": "#1e2028",
    "ts":     "#3a3f4b",
    "warn":   "#ff7043",
}

FONT = ("Consolas"        if platform.system() == "Windows" else
        "Menlo"           if platform.system() == "Darwin"  else
        "DejaVu Sans Mono")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _oi_str(oi):
    if oi >= 1_00_00_000:
        return f"{oi / 1_00_00_000:.1f}Cr"
    if oi >= 1_00_000:
        return f"{oi / 1_00_000:.1f}L"
    if oi >= 1_000:
        return f"{oi / 1_000:.1f}K"
    return str(int(oi))


def _pct(curr, prev):
    return (curr - prev) / prev * 100 if prev else 0.0


def _f(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default




# ── Data fetcher ──────────────────────────────────────────────────────────────
class DataFetcher:
    BASE = "https://api.upstox.com/v2"

    def __init__(self, config):
        self.config  = config
        self._lock   = threading.Lock()
        self.items   = []
        self.ts      = None
        self._idx_px      = {}  # instrument_key → live price (used for ATM calc)
        self._expiry_cache = {}  # instrument_key → expiry date string

    def _hdrs(self):
        return {
            "Authorization": f"Bearer {self.config['upstox_token'].strip()}",
            "Accept":        "application/json",
        }

    def _get(self, path, params=None):
        r = requests.get(
            f"{self.BASE}{path}",
            headers=self._hdrs(),
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    # -- Index quotes (batched) ------------------------------------------------
    def _fetch_quotes(self):
        if not self.config.get("show_indices"):
            return []
        indices = self.config.get("indices", {})
        if not indices:
            return []

        try:
            resp = self._get("/market-quote/quotes",
                             {"instrument_key": ",".join(indices)})
            data = resp.get("data", {})
        except Exception as exc:
            return [{"kind": "ERR", "label": f"Quote API: {exc}"}]

        out = []
        for ikey, label in indices.items():
            try:
                q    = data.get(ikey.replace("|", ":"), {})
                if not q:
                    continue
                lp   = _f(q.get("last_price"))
                ohlc = q.get("ohlc") or {}
                prev = _f(ohlc.get("close"))
                pct  = _pct(lp, prev)
                self._idx_px[ikey] = lp
                out.append({"kind": "INDEX", "label": label, "price": lp, "change": pct})
            except Exception:
                continue
        return out

    # -- Expiry detection (probe forward from today, cache until expired) ------
    def _resolve_expiry(self, ikey):
        today_str = date.today().strftime("%Y-%m-%d")
        cached = self._expiry_cache.get(ikey)
        if cached and cached >= today_str:
            return cached
        for d in range(8):
            expiry = (date.today() + timedelta(days=d)).strftime("%Y-%m-%d")
            try:
                r = self._get("/option/chain", {"instrument_key": ikey, "expiry_date": expiry})
                if r.get("data"):
                    self._expiry_cache[ikey] = expiry
                    return expiry
            except Exception:
                continue
        return None

    # -- Option chains --------------------------------------------------------
    def _fetch_options(self):
        if not self.config.get("show_options"):
            return []
        out = []
        for ikey, cfg in self.config.get("option_chains", {}).items():
            label  = cfg["label"]
            step   = int(cfg["step"])
            n      = int(cfg.get("strikes_around", 2))
            expiry = self._resolve_expiry(ikey)
            if not expiry:
                continue
            curr   = self._idx_px.get(ikey)
            if not curr:
                continue
            atm    = round(curr / step) * step
            wanted = {atm + i * step for i in range(-n, n + 1)}

            try:
                chain = self._get("/option/chain",
                                  {"instrument_key": ikey, "expiry_date": expiry}).get("data", [])
            except Exception:
                continue

            for entry in chain:
                try:
                    strike = _f(entry.get("strike_price"))
                    if strike not in wanted:
                        continue
                    is_atm = (strike == atm)
                    for side, opt_key in (("CE", "call_options"), ("PE", "put_options")):
                        md    = entry.get(opt_key, {}).get("market_data", {})
                        ltp   = _f(md.get("ltp"))
                        if ltp == 0:
                            continue
                        close = _f(md.get("close_price"))
                        oi    = _f(md.get("oi"))
                        pct   = _pct(ltp, close) if close else 0.0
                        out.append({
                            "kind":   side,
                            "label":  f"{label} {int(strike)}{side}",
                            "price":  ltp,
                            "change": pct,
                            "oi":     oi,
                            "strike": strike,
                            "atm":    is_atm,
                        })
                except Exception:
                    continue

        # order: grouped by index label, then ascending strike, CE before PE
        return sorted(out, key=lambda x: (x["label"][:6], x["strike"], x["kind"]))

    # -- Public ---------------------------------------------------------------
    def refresh(self):
        if not self.config.get("upstox_token", "").strip():
            with self._lock:
                self.items = [{"kind": "ERR",
                               "label": "Set upstox_token in ~/.alphaedge_ticker.json"}]
                self.ts = datetime.now()
            return
        items  = self._fetch_quotes()
        items += self._fetch_options()
        with self._lock:
            self.items = items
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

        self._segments  = []
        self._offset    = 0
        self._screen_w  = self.root.winfo_screenwidth()
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
                for k in ("indices", "option_chains"):
                    if k in saved:
                        merged[k] = saved[k]
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

    def _build_ui(self):
        h = self.cfg["height"]
        self._badge = tk.Label(
            self.root, text=" ◈ ALPHAEDGE ",
            bg="#0a1628", fg="#ffd54f",
            font=(FONT, 9, "bold"), padx=0, pady=0, bd=0,
        )
        self._badge.pack(side="left", fill="y")
        self._badge.bind("<Button-3>",  self._show_menu)
        self._badge.bind("<Button-1>",  self._drag_start)
        self._badge.bind("<B1-Motion>", self._drag_do)

        self._cv = tk.Canvas(
            self.root, height=h,
            bg=C["bg"], highlightthickness=0, bd=0,
        )
        self._cv.pack(side="left", fill="x", expand=True)
        self._cv.bind("<Configure>",   self._on_resize)
        self._cv.bind("<Button-1>",    self._drag_start)
        self._cv.bind("<B1-Motion>",   self._drag_do)
        self._cv.bind("<Button-3>",    self._show_menu)

        self._cv.create_line(0, 0, 9999, 0,     fill=C["border"], width=1, tags="border")
        self._cv.create_line(0, h-1, 9999, h-1, fill=C["border"], width=1, tags="border")

        self._ts_lbl = tk.Label(
            self.root, text=" ─── ",
            bg=C["bg"], fg=C["ts"],
            font=(FONT, 8), padx=4, pady=0,
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
            text="⟳  Connecting to Upstox…",
            fill=C["ts"], font=(FONT, self.cfg["font_size"]),
            anchor="w", tags="ticker",
        )

    def _initial_fetch(self):
        self.fetcher.refresh()
        self.root.after(0, self._rebuild)

    # ── Rebuild ───────────────────────────────────────────────────────────────
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
                anchor="w", tags="ticker",
            )
            return

        h  = self.cfg["height"]
        fs = self.cfg["font_size"]
        cy = h // 2 + 1
        sw = self._screen_w or self.root.winfo_screenwidth()
        segs = []

        for item in items:
            kind = item["kind"]

            if kind == "ERR":
                segs.append((f"  ⚠  {item['label']}  ", C["warn"], (FONT, fs)))
                continue

            chg   = item.get("change", 0.0)
            c_chg = C["up"] if chg >= 0 else C["down"]
            arrow = "▲" if chg >= 0 else "▼"
            is_atm = item.get("atm", False)

            if kind == "INDEX":
                c_lbl = C["idx"]
            elif kind == "CE":
                c_lbl = C["ce_atm"] if is_atm else C["ce"]
            else:  # PE
                c_lbl = C["pe_atm"] if is_atm else C["pe"]

            lbl_text = item["label"] + (" ◉" if is_atm else "")
            segs.append((f"  {lbl_text}  ", c_lbl, (FONT, fs, "bold")))
            segs.append((self._fmt(item["price"]), C["price"], (FONT, fs)))
            segs.append((f"  {arrow}{abs(chg):.2f}%", c_chg, (FONT, fs, "bold")))

            if kind in ("CE", "PE"):
                oi = item.get("oi", 0)
                if oi > 0:
                    segs.append((f"  OI:{_oi_str(oi)}", C["meta"], (FONT, fs - 1)))

            segs.append(("   ◆   ", C["sep"], (FONT, fs - 2)))

        cursor_x = sw
        for text, fill, fnt in segs:
            tid = self._cv.create_text(
                cursor_x, cy,
                text=text, fill=fill, font=fnt,
                anchor="w", tags="ticker",
            )
            bbox = self._cv.bbox(tid)
            w = (bbox[2] - bbox[0]) if bbox else max(len(text) * (fs - 1), 1)
            self._segments.append([tid, cursor_x, w])
            cursor_x += w

        self._content_w = max(cursor_x - sw, 1)
        self._offset    = 0
        self._scroll_loop()

    # ── Scroll loop (~60 fps) ─────────────────────────────────────────────────
    def _scroll_loop(self):
        speed = self.cfg["scroll_speed"]
        sw    = self._screen_w or self.root.winfo_screenwidth()
        self._offset += speed

        for seg in self._segments:
            tid, init_x, w = seg
            vx = init_x - self._offset
            if vx + w < 0:
                seg[1] += self._content_w + sw
                vx = seg[1] - self._offset
            cur = self._cv.coords(tid)
            if cur:
                self._cv.coords(tid, vx, cur[1])

        self._after_id = self.root.after(16, self._scroll_loop)

    # ── Format price ─────────────────────────────────────────────────────────
    @staticmethod
    def _fmt(price):
        if price >= 10000:
            return f"{price:,.0f}"
        if price >= 1:
            return f"{price:,.2f}"
        return f"{price:.4f}"

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

    # ── Context menu ──────────────────────────────────────────────────────────
    def _show_menu(self, e):
        m = tk.Menu(self.root, tearoff=0,
                    bg="#141620", fg="#c8cdd4",
                    activebackground="#252838", activeforeground="#ffffff",
                    font=(FONT, 10))
        m.add_command(label="⟳   Refresh Now",    command=self._manual_refresh)
        m.add_separator()
        pos = "Bottom" if self.cfg["position"] == "top" else "Top"
        m.add_command(label=f"↕   Move to {pos}", command=self._toggle_pos)
        m.add_separator()

        for key, on_lbl, off_lbl in [
            ("show_indices", "Hide Indices", "Show Indices"),
            ("show_options", "Hide Options", "Show Options"),
        ]:
            lbl = on_lbl if self.cfg.get(key) else off_lbl
            m.add_command(label=lbl, command=lambda k=key: self._toggle_section(k))
        m.add_separator()

        sm = tk.Menu(m, tearoff=0, bg="#141620", fg="#c8cdd4",
                     activebackground="#252838", activeforeground="#ffffff",
                     font=(FONT, 10))
        for spd, lbl in [(0.8, "Slow"), (1.5, "Normal"), (2.5, "Fast"), (4.0, "Turbo")]:
            dot = "●" if abs(spd - self.cfg["scroll_speed"]) < 0.4 else "○"
            sm.add_command(label=f"{dot}  {lbl}", command=lambda s=spd: self._set_speed(s))
        m.add_cascade(label="⚡  Scroll Speed", menu=sm)

        om = tk.Menu(m, tearoff=0, bg="#141620", fg="#c8cdd4",
                     activebackground="#252838", activeforeground="#ffffff",
                     font=(FONT, 10))
        for op, lbl in [(0.6, "60%"), (0.8, "80%"), (0.96, "96%"), (1.0, "100%")]:
            dot = "●" if abs(op - self.cfg["opacity"]) < 0.05 else "○"
            om.add_command(label=f"{dot}  {lbl}", command=lambda o=op: self._set_opacity(o))
        m.add_cascade(label="◐   Opacity", menu=om)
        m.add_separator()
        m.add_command(label="✕   Quit", command=self._quit)
        m.post(e.x_root, e.y_root)

    def _manual_refresh(self):
        threading.Thread(
            target=lambda: (self.fetcher.refresh(), self.root.after(0, self._rebuild)),
            daemon=True,
        ).start()

    def _toggle_pos(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        h  = self.cfg["height"]
        if self.cfg["position"] == "top":
            self.cfg["position"] = "bottom"
            self.root.geometry(f"{sw}x{h}+0+{sh-h-1}")
        else:
            self.cfg["position"] = "top"
            self.root.geometry(f"{sw}x{h}+0+0")
        self._save_cfg()

    def _toggle_section(self, key):
        self.cfg[key] = not self.cfg.get(key, True)
        self._save_cfg()
        self._manual_refresh()

    def _set_speed(self, s):
        self.cfg["scroll_speed"] = s
        self._save_cfg()

    def _set_opacity(self, o):
        self.cfg["opacity"] = o
        self._save_cfg()
        try:
            self.root.attributes("-alpha", o)
        except Exception:
            pass

    def _schedule_refresh(self):
        self.root.after(self.cfg["refresh_interval"] * 1000, self._bg_refresh)

    def _bg_refresh(self):
        threading.Thread(
            target=lambda: (self.fetcher.refresh(), self.root.after(0, self._rebuild)),
            daemon=True,
        ).start()
        self._schedule_refresh()

    def _quit(self):
        self._save_cfg()
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self.root.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AlphaEdge Ticker v2.0")
    print("  NSE/BSE Indices · Options (Upstox)")
    print("=" * 60)
    print(f"  Platform : {platform.system()} {platform.release()}")
    print(f"  Config   : {CONFIG_FILE}")
    print()
    if not os.path.exists(CONFIG_FILE):
        print("  First run — no config found.")
        print(f"  Edit {CONFIG_FILE}")
        print("  and set your upstox_token before starting.")
        print()
    print("  Right-click for options  |  Esc to quit")
    print("=" * 60)
    TickerBanner()
