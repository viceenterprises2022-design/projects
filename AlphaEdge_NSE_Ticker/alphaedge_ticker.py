#!/usr/bin/env python3
"""
AlphaEdge Ticker v3.0 — Three-row NSE/BSE Indices · Options via Upstox
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

# ── Row definitions — order = top→bottom ──────────────────────────────────────
# strikes_around: how many strikes each side of ATM (±300 pts → step/300 strikes)
ROW_DEFS = [
    {"ikey": "NSE_INDEX|Nifty 50",   "label": "NIFTY",  "step": 50,  "strikes_around": 6},
    {"ikey": "NSE_INDEX|Nifty Bank", "label": "BNKN",   "step": 100, "strikes_around": 3},
    {"ikey": "BSE_INDEX|SENSEX",     "label": "SENSEX", "step": 100, "strikes_around": 3},
]

# ── Default config ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "upstox_token":     "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9.lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo",
    "position":         "bottom",
    "height":           28,
    "scroll_speed":     3.0,
    "refresh_interval": 30,
    "font_size":        11,
    "opacity":          0.96,
}

# ── Colours ───────────────────────────────────────────────────────────────────
C = {
    "bg":     "#0d0d0f",
    "idx":    "#ffd54f",
    "ce":     "#a5d6a7",
    "pe":     "#ef9a9a",
    "ce_atm": "#69f0ae",
    "pe_atm": "#ff5252",
    "price":  "#c8cdd4",
    "up":     "#00e676",
    "down":   "#ff4444",
    "meta":   "#8a8f9a",
    "sep":    "#353945",
    "border": "#1e2028",
    "ts":     "#3a3f4b",
    "warn":   "#ff7043",
}

# Badge foreground per row (NIFTY=gold, BNKN=green, SENSEX=rose)
ROW_FG = ["#ffd54f", "#69f0ae", "#ef9a9a"]

FONT = ("Consolas"        if platform.system() == "Windows" else
        "Menlo"           if platform.system() == "Darwin"  else
        "DejaVu Sans Mono")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _oi_str(oi):
    if oi >= 1_00_00_000: return f"{oi/1_00_00_000:.1f}Cr"
    if oi >= 1_00_000:    return f"{oi/1_00_000:.1f}L"
    if oi >= 1_000:       return f"{oi/1_000:.1f}K"
    return str(int(oi))

def _pct(curr, prev):
    return (curr - prev) / prev * 100 if prev else 0.0

def _f(val, default=0.0):
    try:    return float(val) if val is not None else default
    except: return default


# ── Data fetcher ──────────────────────────────────────────────────────────────
class DataFetcher:
    BASE = "https://api.upstox.com/v2"

    def __init__(self, config):
        self.config        = config
        self._lock         = threading.Lock()
        self._snapshot     = {}   # ikey → [items]  (swapped atomically after refresh)
        self.ts            = None
        self._idx_px       = {}   # ikey → live price; written only from refresh thread
        self._expiry_cache = {}   # ikey → expiry date string

    def _hdrs(self):
        return {
            "Authorization": f"Bearer {self.config['upstox_token'].strip()}",
            "Accept":        "application/json",
        }

    def _get(self, path, params=None):
        r = requests.get(
            f"{self.BASE}{path}", headers=self._hdrs(), params=params, timeout=10,
        )
        r.raise_for_status()
        return r.json()

    # -- Index quotes (batched) ------------------------------------------------
    def _fetch_quotes(self, out):
        ikeys = [rd["ikey"] for rd in ROW_DEFS]
        try:
            resp = self._get("/market-quote/quotes", {"instrument_key": ",".join(ikeys)})
            data = resp.get("data", {})
        except Exception as exc:
            for rd in ROW_DEFS:
                out[rd["ikey"]] = [{"kind": "ERR", "label": f"Quote: {exc}"}]
            return

        for rd in ROW_DEFS:
            ikey = rd["ikey"]
            try:
                q    = data.get(ikey.replace("|", ":"), {})
                if not q:
                    out[ikey] = []
                    continue
                lp   = _f(q.get("last_price"))
                prev = _f((q.get("ohlc") or {}).get("close"))
                self._idx_px[ikey] = lp
                out[ikey] = [{"kind": "INDEX", "label": rd["label"],
                               "price": lp, "change": _pct(lp, prev)}]
            except Exception:
                out[ikey] = []

    # -- Expiry auto-detection (probe forward up to 8 days) --------------------
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

    # -- Option chains (±300 pts = strikes_around strikes each side) -----------
    def _fetch_options(self, out):
        for rd in ROW_DEFS:
            ikey   = rd["ikey"]
            step   = int(rd["step"])
            n      = int(rd["strikes_around"])
            curr   = self._idx_px.get(ikey)
            expiry = self._resolve_expiry(ikey)
            if not expiry or not curr:
                continue
            atm    = round(curr / step) * step
            wanted = {atm + i * step for i in range(-n, n + 1)}

            try:
                chain = self._get(
                    "/option/chain",
                    {"instrument_key": ikey, "expiry_date": expiry},
                ).get("data", [])
            except Exception:
                continue

            opts = []
            for entry in chain:
                try:
                    strike = _f(entry.get("strike_price"))
                    if strike not in wanted:
                        continue
                    is_atm = strike == atm
                    for side, opt_key in (("CE", "call_options"), ("PE", "put_options")):
                        md    = entry.get(opt_key, {}).get("market_data", {})
                        ltp   = _f(md.get("ltp"))
                        if ltp == 0:
                            continue
                        close = _f(md.get("close_price"))
                        oi    = _f(md.get("oi"))
                        opts.append({
                            "kind":   side,
                            "label":  f"{rd['label']} {int(strike)}{side}",
                            "price":  ltp,
                            "change": _pct(ltp, close) if close else 0.0,
                            "oi":     oi,
                            "strike": strike,
                            "atm":    is_atm,
                        })
                except Exception:
                    continue

            # ascending strike, CE before PE within each strike
            opts.sort(key=lambda x: (x["strike"], x["kind"]))
            out[ikey] = out.get(ikey, []) + opts

    # -- Public ----------------------------------------------------------------
    def refresh(self):
        if not self.config.get("upstox_token", "").strip():
            err = [{"kind": "ERR", "label": "Set upstox_token in ~/.alphaedge_ticker.json"}]
            with self._lock:
                self._snapshot = {rd["ikey"]: err[:] for rd in ROW_DEFS}
                self.ts = datetime.now()
            return

        out = {rd["ikey"]: [] for rd in ROW_DEFS}
        self._fetch_quotes(out)
        self._fetch_options(out)
        with self._lock:
            self._snapshot = out
            self.ts = datetime.now()

    def get(self):
        with self._lock:
            return dict(self._snapshot), self.ts


# ── Banner window — three stacked rows ────────────────────────────────────────
class TickerBanner:
    def __init__(self):
        self.cfg      = self._load_cfg()
        self.fetcher  = DataFetcher(self.cfg)
        self.root     = tk.Tk()
        self.root.title("AlphaEdge Ticker")
        self._rows    = []
        self._screen_w = 0
        self._dx = self._dy = 0

        self._setup_window()
        self._build_ui()
        self._set_loading_all()
        threading.Thread(target=self._initial_fetch, daemon=True).start()
        self._schedule_refresh()
        self.root.mainloop()

    # ── Config ────────────────────────────────────────────────────────────────
    def _load_cfg(self):
        if os.path.exists(CONFIG_FILE):
            try:
                saved = json.load(open(CONFIG_FILE))
                return {**DEFAULT_CONFIG, **saved}
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
        total_h = h * len(ROW_DEFS)
        y = 0 if self.cfg["position"] == "top" else sh - total_h - 1
        self.root.geometry(f"{sw}x{total_h}+0+{y}")
        self._screen_w = sw

    def _build_ui(self):
        h = self.cfg["height"]
        n = len(ROW_DEFS)
        for i, rd in enumerate(ROW_DEFS):
            frame = tk.Frame(self.root, bg=C["bg"], height=h)
            frame.pack(side="top", fill="x")
            frame.pack_propagate(False)

            badge = tk.Label(
                frame, text=f" ◈ {rd['label']} ",
                bg="#0a1628", fg=ROW_FG[i],
                font=(FONT, 9, "bold"), padx=0, pady=0, bd=0,
            )
            badge.pack(side="left", fill="y")

            # Timestamp only on last row, right side
            ts_lbl = None
            if i == n - 1:
                ts_lbl = tk.Label(
                    frame, text=" ─── ",
                    bg=C["bg"], fg=C["ts"],
                    font=(FONT, 8), padx=4, pady=0,
                )
                ts_lbl.pack(side="right", fill="y")
                ts_lbl.bind("<Button-3>",  self._show_menu)
                ts_lbl.bind("<Button-1>",  self._drag_start)
                ts_lbl.bind("<B1-Motion>", self._drag_do)

            cv = tk.Canvas(
                frame, height=h,
                bg=C["bg"], highlightthickness=0, bd=0,
            )
            cv.pack(side="left", fill="x", expand=True)
            cv.create_line(0, 0, 9999, 0,     fill=C["border"], width=1, tags="border")
            cv.create_line(0, h-1, 9999, h-1, fill=C["border"], width=1, tags="border")
            cv.bind("<Configure>", self._on_resize)

            for w in (badge, cv, frame):
                w.bind("<Button-3>",  self._show_menu)
                w.bind("<Button-1>",  self._drag_start)
                w.bind("<B1-Motion>", self._drag_do)

            self._rows.append({
                "ikey":      rd["ikey"],
                "canvas":    cv,
                "ts_lbl":    ts_lbl,
                "segments":  [],
                "offset":    0.0,
                "content_w": 1,
                "after_id":  None,
            })

        self.root.bind("<Escape>", lambda e: self._quit())

    def _on_resize(self, event):
        self._screen_w = event.width

    # ── Loading state ─────────────────────────────────────────────────────────
    def _set_loading_all(self):
        for row in self._rows:
            self._set_loading_row(row)

    def _set_loading_row(self, row):
        h  = self.cfg["height"]
        cv = row["canvas"]
        cv.delete("ticker")
        cv.create_text(
            120, h // 2 + 1,
            text="⟳  Connecting to Upstox…",
            fill=C["ts"], font=(FONT, self.cfg["font_size"]),
            anchor="w", tags="ticker",
        )

    # ── Fetch ─────────────────────────────────────────────────────────────────
    def _initial_fetch(self):
        self.fetcher.refresh()
        self.root.after(0, self._rebuild_all)

    # ── Rebuild ───────────────────────────────────────────────────────────────
    def _rebuild_all(self):
        snapshot, ts = self.fetcher.get()
        if ts:
            for row in self._rows:
                if row["ts_lbl"]:
                    row["ts_lbl"].config(text=ts.strftime(" %H:%M:%S "), fg=C["ts"])
        for row in self._rows:
            self._rebuild_row(row, snapshot.get(row["ikey"], []))

    def _rebuild_row(self, row, items):
        cv = row["canvas"]
        if row["after_id"]:
            self.root.after_cancel(row["after_id"])
            row["after_id"] = None

        cv.delete("ticker")
        row["segments"] = []

        h  = self.cfg["height"]
        fs = self.cfg["font_size"]
        cy = h // 2 + 1
        sw = self._screen_w or self.root.winfo_screenwidth()

        if not items:
            cv.create_text(
                120, cy, text="⚠  No data",
                fill=C["down"], font=(FONT, fs), anchor="w", tags="ticker",
            )
            return

        segs = []
        for item in items:
            kind   = item["kind"]
            if kind == "ERR":
                segs.append((f"  ⚠  {item['label']}  ", C["warn"], (FONT, fs)))
                continue

            chg    = item.get("change", 0.0)
            c_chg  = C["up"] if chg >= 0 else C["down"]
            arrow  = "▲" if chg >= 0 else "▼"
            is_atm = item.get("atm", False)

            if kind == "INDEX":
                c_lbl = C["idx"]
            elif kind == "CE":
                c_lbl = C["ce_atm"] if is_atm else C["ce"]
            else:
                c_lbl = C["pe_atm"] if is_atm else C["pe"]

            lbl_text = item["label"] + (" ◉" if is_atm else "")
            segs.append((f"  {lbl_text}  ", c_lbl, (FONT, fs, "bold")))
            segs.append((self._fmt(item["price"]), C["price"], (FONT, fs)))
            segs.append((f"  {arrow}{abs(chg):.2f}%", c_chg, (FONT, fs, "bold")))

            if kind in ("CE", "PE") and item.get("oi", 0) > 0:
                segs.append((f"  OI:{_oi_str(item['oi'])}", C["meta"], (FONT, fs - 1)))

            segs.append(("   ◆   ", C["sep"], (FONT, fs - 2)))

        cursor_x = sw
        for text, fill, fnt in segs:
            tid  = cv.create_text(cursor_x, cy, text=text, fill=fill, font=fnt,
                                   anchor="w", tags="ticker")
            bbox = cv.bbox(tid)
            w    = (bbox[2] - bbox[0]) if bbox else max(len(text) * (fs - 1), 1)
            row["segments"].append([tid, cursor_x, w])
            cursor_x += w

        row["content_w"] = max(cursor_x - sw, 1)
        row["offset"]    = 0.0
        self._scroll_row(row)

    # ── Per-row scroll loop (~60 fps) ─────────────────────────────────────────
    def _scroll_row(self, row):
        speed = self.cfg["scroll_speed"]
        sw    = self._screen_w or self.root.winfo_screenwidth()
        cv    = row["canvas"]
        row["offset"] += speed

        for seg in row["segments"]:
            tid, init_x, w = seg
            vx = init_x - row["offset"]
            if vx + w < 0:
                seg[1] += row["content_w"] + sw
                vx = seg[1] - row["offset"]
            cur = cv.coords(tid)
            if cur:
                cv.coords(tid, vx, cur[1])

        row["after_id"] = self.root.after(16, lambda r=row: self._scroll_row(r))

    # ── Format price ─────────────────────────────────────────────────────────
    @staticmethod
    def _fmt(price):
        if price >= 10000: return f"{price:,.0f}"
        if price >= 1:     return f"{price:,.2f}"
        return f"{price:.4f}"

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_do(self, e):
        sw      = self.root.winfo_screenwidth()
        sh      = self.root.winfo_screenheight()
        total_h = self.cfg["height"] * len(ROW_DEFS)
        ny      = max(0, min(sh - total_h, e.y_root - self._dy))
        self.root.geometry(f"{sw}x{total_h}+0+{ny}")
        self.cfg["position"] = "top" if ny < sh // 2 else "bottom"

    # ── Context menu ──────────────────────────────────────────────────────────
    def _show_menu(self, e):
        m = tk.Menu(self.root, tearoff=0,
                    bg="#141620", fg="#c8cdd4",
                    activebackground="#252838", activeforeground="#ffffff",
                    font=(FONT, 10))
        m.add_command(label="⟳   Refresh Now", command=self._manual_refresh)
        m.add_separator()
        pos = "Bottom" if self.cfg["position"] == "top" else "Top"
        m.add_command(label=f"↕   Move to {pos}", command=self._toggle_pos)
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
            target=lambda: (self.fetcher.refresh(), self.root.after(0, self._rebuild_all)),
            daemon=True,
        ).start()

    def _toggle_pos(self):
        sw      = self.root.winfo_screenwidth()
        sh      = self.root.winfo_screenheight()
        total_h = self.cfg["height"] * len(ROW_DEFS)
        if self.cfg["position"] == "top":
            self.cfg["position"] = "bottom"
            self.root.geometry(f"{sw}x{total_h}+0+{sh-total_h-1}")
        else:
            self.cfg["position"] = "top"
            self.root.geometry(f"{sw}x{total_h}+0+0")
        self._save_cfg()

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
            target=lambda: (self.fetcher.refresh(), self.root.after(0, self._rebuild_all)),
            daemon=True,
        ).start()
        self._schedule_refresh()

    def _quit(self):
        self._save_cfg()
        for row in self._rows:
            if row["after_id"]:
                self.root.after_cancel(row["after_id"])
        self.root.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AlphaEdge Ticker v3.0")
    print("  Three-row NSE/BSE Indices · Options (Upstox)")
    print("=" * 60)
    print(f"  Platform : {platform.system()} {platform.release()}")
    print(f"  Config   : {CONFIG_FILE}")
    print()
    if not os.path.exists(CONFIG_FILE):
        print("  First run — no config found.")
        print(f"  Edit {CONFIG_FILE} and set your upstox_token.")
        print()
    print("  Right-click for options  |  Esc to quit")
    print("=" * 60)
    TickerBanner()
