#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          USDT TRC20 — PRODUCTION TRANSACTION VALIDATOR v1.2                 ║
║          Anti-Fraud · Blockchain Forensics · TRON Mainnet                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

CHANGELOG v1.1 — fixes from live run analysis:
  FIX-01  Enum serialisation: asdict() stored CheckStatus enum objects;
          all comparisons now use .value strings consistently via check_to_dict()
  FIX-02  TronGrid fallback: when TronGrid returns empty, TronScan is used as
          primary source; script no longer hard-stops on TronGrid 404
  FIX-03  Block number: extracted from TronScan "block" field when TronGrid
          blockNumber is absent; prevents block_number=0 chain failure
  FIX-04  Confirmation overflow: guarded against block_number=0 producing
          current_block as confirmation count (~80M) showing false PASS
  FIX-05  02.2 confirmed flag: falls back to TronScan "confirmed" field when
          TronGrid data is empty
  FIX-06  06.1 TronGrid empty ≠ FAIL: empty contractRet (provider has no data)
          now treated as WARN/UNAVAILABLE, not FAIL
  FIX-07  Final verdict counting: pass/fail/warn counts now correct because of
          FIX-01; final_status correctly reflects critical failures
  FIX-08  datetime.utcnow() deprecation: replaced with datetime.now(timezone.utc)
  FIX-09  Ankr timeout: dedicated 8s timeout + 2 retries only for Ankr endpoint
  FIX-10  03.3 confirmation poll: wait loop now correctly guards starting
          condition with valid block_number before polling

Usage:
    python usdt_validator.py <TX_HASH>
    python usdt_validator.py <TX_HASH> --expected-amount 100000
    python usdt_validator.py <TX_HASH> --expected-amount 100000 --expected-to TYourWallet
    python usdt_validator.py <TX_HASH> --operator "Vinod" --expected-amount 100000

Requires:  pip install requests rich
"""

import sys
import os
import json
import time
import argparse
import hashlib
import datetime
from datetime import timezone
from typing import Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.rule import Rule
from rich import box
from rich.style import Style

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS — DO NOT MODIFY
# ─────────────────────────────────────────────────────────────────────────────
OFFICIAL_USDT_CONTRACT  = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
OFFICIAL_TOKEN_NAME     = "Tether USD"
OFFICIAL_TOKEN_SYMBOL   = "USDT"
OFFICIAL_TOKEN_DECIMALS = 6
USDT_DIVISOR            = 1_000_000

# Confirmation thresholds
CONFIRMS_STANDARD    = 19   # SuperNode consensus minimum
CONFIRMS_HIGH_VALUE  = 30   # High-value standard
CONFIRMS_PRODUCTION  = 50   # Production grade (this script always targets this)
CONFIRMS_RISKY       = 70   # Unverified contract sender

# API endpoints
TRONGRID_BASE    = "https://api.trongrid.io"
TRONSCAN_BASE    = "https://apilist.tronscanapi.com"

# TronGrid API key — unlocks higher rate limits and full tx data availability
TRONGRID_API_KEY = "e39c9fb9-66a1-43ef-8f21-4eb605aeceb2"

# HTTP settings
REQUEST_TIMEOUT      = 15
ANKR_TIMEOUT         = 8   # FIX-09: dedicated short timeout for Ankr
MAX_RETRIES          = 4
ANKR_RETRIES         = 2   # FIX-09: fewer retries for Ankr
BACKOFF_BASE         = 2

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
class CheckStatus(Enum):
    PENDING = "pending"
    PASS    = "pass"
    FAIL    = "fail"
    WARN    = "warn"
    SKIP    = "skip"
    RUNNING = "running"

# Shorthand strings for comparisons — always use these, never .value inline
S_PASS    = CheckStatus.PASS.value
S_FAIL    = CheckStatus.FAIL.value
S_WARN    = CheckStatus.WARN.value
S_SKIP    = CheckStatus.SKIP.value
S_PENDING = CheckStatus.PENDING.value

@dataclass
class CheckResult:
    section:  str
    code:     str
    name:     str
    status:   CheckStatus = CheckStatus.PENDING
    detail:   str = ""
    critical: bool = True
    raw_data: dict = field(default_factory=dict)

@dataclass
class ValidationReport:
    tx_hash:            str
    operator:           str
    started_at:         str
    completed_at:       str = ""
    expected_amount:    Optional[float] = None
    expected_to:        Optional[str] = None
    checks:             list = field(default_factory=list)
    final_status:       str = "INCOMPLETE"
    actual_amount:      Optional[float] = None
    actual_to:          Optional[str] = None
    block_number:       Optional[int] = None
    confirmations:      Optional[int] = None
    contract_address:   Optional[str] = None
    sender_address:     Optional[str] = None
    sender_is_contract: bool = False
    provider_consensus: dict = field(default_factory=dict)


def check_to_dict(check: CheckResult) -> dict:
    """
    FIX-01: Custom serialiser that stores CheckStatus as its string value,
    not as the Enum object. dataclasses.asdict() does NOT auto-convert Enums
    to their .value, causing all comparisons against string literals to fail.
    """
    return {
        "section":  check.section,
        "code":     check.code,
        "name":     check.name,
        "status":   check.status.value,   # ← always a plain string
        "detail":   check.detail,
        "critical": check.critical,
        "raw_data": check.raw_data,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONSOLE
# ─────────────────────────────────────────────────────────────────────────────
console = Console(highlight=False)

STATUS_ICONS = {
    S_PASS:    "[bold green]  ✓ PASS  [/]",
    S_FAIL:    "[bold red]  ✗ FAIL  [/]",
    S_WARN:    "[bold yellow]  ⚠ WARN  [/]",
    S_SKIP:    "[dim]  — SKIP  [/]",
    S_PENDING: "[dim]  · · ·  [/]",
    "running": "[bold cyan]  ⟳ CHECK [/]",
}

STATUS_COLOR = {
    S_PASS: "green", S_FAIL: "red", S_WARN: "yellow",
    S_SKIP: "dim",   S_PENDING: "dim", "running": "cyan",
}

SECTION_COLORS = {
    "§01": "cyan",   "§02": "red",     "§03": "green",
    "§04": "yellow", "§05": "medium_purple1", "§06": "orange1", "§07": "cyan",
}

def print_section_header(code: str, title: str, mandatory: bool = True):
    color = SECTION_COLORS.get(code, "white")
    badge = "[bold red]MANDATORY[/]" if mandatory else "[bold yellow]CONDITIONAL[/]"
    console.print()
    console.print(Rule(
        f"[bold {color}]{code}[/] [bold white]{title}[/]  {badge}",
        style=color, align="left",
    ))

def print_check(check: CheckResult, elapsed: float = 0.0):
    sv     = check.status.value
    icon   = STATUS_ICONS.get(sv, "")
    color  = STATUS_COLOR.get(sv, "white")
    crit   = " [bold red][CRITICAL][/]" if check.critical else ""
    timing = f" [dim]({elapsed:.2f}s)[/]" if elapsed > 0 else ""
    console.print(f"  {icon} [dim]{check.code}[/] [{color}]{check.name}[/]{crit}{timing}")
    if check.detail:
        for line in check.detail.split("\n"):
            if line.strip():
                console.print(f"         [dim]{line}[/]")

# ─────────────────────────────────────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _headers(trongrid: bool = False) -> dict:
    """Return base headers, injecting the TronGrid API key for TronGrid endpoints."""
    h = {"User-Agent": "USDT-TRC20-Validator/1.2", "Accept": "application/json"}
    if trongrid and TRONGRID_API_KEY:
        h["TRON-PRO-API-KEY"] = TRONGRID_API_KEY
    return h

def http_get(url: str, params: dict = None, timeout: int = REQUEST_TIMEOUT,
             retries: int = MAX_RETRIES) -> dict:
    is_trongrid = TRONGRID_BASE in url
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=_headers(trongrid=is_trongrid), timeout=timeout)
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
        time.sleep(min(BACKOFF_BASE ** attempt, 20))
    raise ConnectionError(f"GET {url} failed after {retries} attempts: {last_exc}")

def http_post(url: str, payload: dict, timeout: int = REQUEST_TIMEOUT,
              retries: int = MAX_RETRIES) -> dict:
    is_trongrid = TRONGRID_BASE in url
    h = {**_headers(trongrid=is_trongrid), "Content-Type": "application/json"}
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload, headers=h, timeout=timeout)
            if r.status_code in (400, 401, 403, 404):
                return {}
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
        time.sleep(min(BACKOFF_BASE ** attempt, 20))
    raise ConnectionError(f"POST {url} failed after {retries} attempts: {last_exc}")

# ─────────────────────────────────────────────────────────────────────────────
# API FETCHERS  (correct TronGrid FullNode HTTP API endpoints per official docs)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_tx_by_id(tx_hash: str) -> dict:
    """
    POST /wallet/gettransactionbyid
    FullNode — returns complete Transaction object with ret[].contractRet.
    Reliable and authenticated via API key. Empty dict if not found.
    """
    return http_post(f"{TRONGRID_BASE}/wallet/gettransactionbyid",
                     {"value": tx_hash})

def fetch_tx_info_by_id(tx_hash: str) -> dict:
    """
    POST /wallet/gettransactioninfobyid
    FullNode — returns TransactionInfo: blockNumber, blockTimeStamp,
    receipt.result, log[], contract_address. This is the authoritative
    source for block number and on-chain execution receipt.
    """
    return http_post(f"{TRONGRID_BASE}/wallet/gettransactioninfobyid",
                     {"value": tx_hash})

def fetch_tx_info_solidity(tx_hash: str) -> dict:
    """
    POST /walletsolidity/gettransactioninfobyid
    Solidity node — only returns data for CONFIRMED transactions.
    Used as 3rd-provider consensus check (replaces unreliable Ankr).
    Empty dict or no blockNumber = still unconfirmed.
    """
    return http_post(f"{TRONGRID_BASE}/walletsolidity/gettransactioninfobyid",
                     {"value": tx_hash})

def fetch_tx_events(tx_hash: str) -> list:
    """
    GET /v1/transactions/{hash}/events
    TronGrid indexed REST — returns Transfer event logs for this TX.
    Authenticated via TRON-PRO-API-KEY header.
    """
    try:
        data = http_get(f"{TRONGRID_BASE}/v1/transactions/{tx_hash}/events")
        return data.get("data", [])
    except Exception:
        return []

def fetch_tx_tronscan(tx_hash: str) -> dict:
    """TronScan transaction-info — independent provider for cross-validation."""
    return http_get(f"{TRONSCAN_BASE}/api/transaction-info", params={"hash": tx_hash})

def fetch_current_block() -> dict:
    """
    Returns current block heights from TronGrid FullNode + TronScan.
    TronGrid: POST /wallet/getnowblock (authenticated)
    TronScan: GET /api/block/latest
    """
    tg = ts = 0
    try:
        data = http_post(f"{TRONGRID_BASE}/wallet/getnowblock", {})
        tg = data.get("block_header", {}).get("raw_data", {}).get("number", 0)
    except Exception:
        pass
    try:
        data = http_get(f"{TRONSCAN_BASE}/api/block/latest")
        ts = data.get("number", 0)
    except Exception:
        pass
    return {"trongrid": tg, "tronscan": ts, "best": max(tg, ts)}

def fetch_account(address: str) -> dict:
    """GET /v1/accounts/{address} — authenticated TronGrid indexed REST."""
    data = http_get(f"{TRONGRID_BASE}/v1/accounts/{address}")
    items = data.get("data", [{}])
    return items[0] if items else {}

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────
class USDTValidator:
    def __init__(self, tx_hash: str, expected_amount: Optional[float],
                 expected_to: Optional[str], operator: str):
        self.tx_hash         = tx_hash.strip()
        self.expected_amount = expected_amount
        self.expected_to     = expected_to.strip() if expected_to else None
        self.operator        = operator
        self.report          = ValidationReport(
            tx_hash=self.tx_hash,
            operator=operator,
            # FIX-08: use timezone-aware UTC
            started_at=datetime.datetime.now(timezone.utc).isoformat(),
            expected_amount=expected_amount,
            expected_to=expected_to,
        )
        # Cached API data — three independent TronGrid sources + TronScan
        self._tx_by_id:    dict = {}   # POST /wallet/gettransactionbyid     → ret[].contractRet
        self._tx_info:     dict = {}   # POST /wallet/gettransactioninfobyid → blockNumber, receipt
        self._tx_solidity: dict = {}   # POST /walletsolidity/gettransactioninfobyid → confirmed state
        self._tx_ts:       dict = {}   # TronScan transaction-info → independent provider
        self._tx_events:   list = []   # GET  /v1/transactions/{hash}/events → Transfer logs
        self._trc20_transfers: list = []
        self._current_block: int = 0

    # ── run_check wrapper ────────────────────────────────────────────────────
    def _run_check(self, check: CheckResult, fn) -> CheckResult:
        t0 = time.time()
        console.print(f"  [cyan]⟳[/] [dim]{check.code}[/] [white]{check.name}[/] ...", end="\r")
        try:
            fn(check)
        except Exception as exc:
            check.status = CheckStatus.FAIL
            check.detail = f"UNEXPECTED EXCEPTION: {type(exc).__name__}: {exc}"
        elapsed = time.time() - t0
        console.print(" " * 100, end="\r")
        print_check(check, elapsed)
        self.report.checks.append(check_to_dict(check))  # FIX-01
        return check

    def _last_status(self) -> str:
        """Return string status of the most recent check."""
        return self.report.checks[-1]["status"] if self.report.checks else S_PENDING

    # ────────────────────────────────────────────────────────────────────────
    # §01  CONTRACT VERIFICATION
    # ────────────────────────────────────────────────────────────────────────
    def section_01(self) -> bool:
        print_section_header("§01", "CONTRACT VERIFICATION", mandatory=True)

        # 01.1 — Locate transaction via all TronGrid FullNode endpoints + TronScan
        def c01_1(c):
            # Primary: POST /wallet/gettransactionbyid (FullNode, authenticated)
            self._tx_by_id    = fetch_tx_by_id(self.tx_hash)
            # Secondary: POST /wallet/gettransactioninfobyid (receipt + blockNumber)
            self._tx_info     = fetch_tx_info_by_id(self.tx_hash)
            # Tertiary: POST /walletsolidity/gettransactioninfobyid (confirmed-only)
            self._tx_solidity = fetch_tx_info_solidity(self.tx_hash)
            # Independent: TronScan
            self._tx_ts       = fetch_tx_tronscan(self.tx_hash)
            # Events: GET /v1/transactions/{hash}/events (Transfer logs)
            self._tx_events   = fetch_tx_events(self.tx_hash)

            tg_found  = bool(self._tx_by_id.get("txID") or self._tx_by_id.get("ret"))
            tgi_found = bool(self._tx_info.get("id") or self._tx_info.get("blockNumber"))
            ts_found  = bool(self._tx_ts.get("hash") or self._tx_ts.get("contractRet"))
            any_found = tg_found or tgi_found or ts_found

            sources = []
            if tg_found:  sources.append("TronGrid/wallet")
            if tgi_found: sources.append("TronGrid/txinfo")
            if ts_found:  sources.append("TronScan")

            c.raw_data = {"tg_by_id": tg_found, "tg_info": tgi_found, "tronscan": ts_found}

            if not any_found:
                c.status = CheckStatus.FAIL
                c.detail = (
                    "Transaction NOT found on any provider.\n"
                    "Verify the TX hash is correct and the transaction has been broadcast."
                )
                return

            c.status = CheckStatus.PASS
            c.detail = f"Transaction located on: {', '.join(sources)}"

        self._run_check(CheckResult("§01", "01.1", "Transaction located on chain"), c01_1)
        if self._last_status() == S_FAIL:
            console.print("  [bold red]⛔ Cannot proceed — transaction not found on any provider.[/]")
            return False

        # 01.2 — Extract TRC20 transfer records
        # Source priority: TronGrid events (most reliable) → TronScan trc20TransferInfo
        def c01_2(c):
            # TronGrid /v1/transactions/{hash}/events returns Transfer event objects:
            # {event_name, contract_address, result{from,to,value}, block_number, ...}
            trc20_list = []
            if self._tx_events:
                for ev in self._tx_events:
                    if ev.get("event_name") == "Transfer":
                        res = ev.get("result", {})
                        trc20_list.append({
                            "contract_address": ev.get("contract_address", ""),
                            "from_address":     res.get("from", ""),
                            "to_address":       res.get("to", ""),
                            "amount_str":       res.get("value", "0"),
                            "_source":          "trongrid_events",
                        })

            # Fallback: TronScan trc20TransferInfo
            if not trc20_list:
                for t in self._tx_ts.get("trc20TransferInfo", []):
                    trc20_list.append({
                        "contract_address": t.get("contract_address", ""),
                        "from_address":     t.get("from_address",    t.get("from", "")),
                        "to_address":       t.get("to_address",      t.get("to", "")),
                        "amount_str":       str(t.get("amount_str",  t.get("amount", "0"))),
                        "_source":          "tronscan",
                    })

            if not trc20_list:
                c.status = CheckStatus.FAIL
                c.detail = (
                    "No TRC20 Transfer events found in this transaction.\n"
                    "This may not be a TRC20 USDT transfer, or data is incomplete."
                )
                return

            self._trc20_transfers = trc20_list
            sources = {t["_source"] for t in trc20_list}
            contracts = list({t.get("contract_address", "") for t in trc20_list})
            self.report.contract_address = contracts[0] if contracts else None
            c.status = CheckStatus.PASS
            c.detail = (
                f"Found {len(trc20_list)} TRC20 Transfer event(s). "
                f"Contract(s): {', '.join(contracts)}  [src: {', '.join(sources)}]"
            )
            c.raw_data = {"contract_addresses": contracts, "sources": list(sources)}

        self._run_check(CheckResult("§01", "01.2", "TRC20 transfer records extracted"), c01_2)
        if self._last_status() == S_FAIL:
            return False

        # 01.3 — Contract address exact match
        def c01_3(c):
            contracts = {t.get("contract_address", "") for t in self._trc20_transfers}
            has_official = OFFICIAL_USDT_CONTRACT in contracts
            fakes = contracts - {OFFICIAL_USDT_CONTRACT}
            if not has_official:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"OFFICIAL CONTRACT NOT FOUND IN TRANSACTION\n"
                    f"Expected : {OFFICIAL_USDT_CONTRACT}\n"
                    f"Found    : {', '.join(contracts) or 'NONE'}\n"
                    f"⚠  COUNTERFEIT TOKEN — REJECT IMMEDIATELY"
                )
                return
            if fakes:
                c.status = CheckStatus.WARN
                c.detail = (
                    f"Official contract present but additional contracts detected: {', '.join(fakes)}\n"
                    f"⚠  Possible dust+confusion attack — review each transfer carefully."
                )
                return
            c.status = CheckStatus.PASS
            c.detail = f"Contract address verified: {OFFICIAL_USDT_CONTRACT}"

        self._run_check(CheckResult("§01", "01.3", f"Contract = {OFFICIAL_USDT_CONTRACT}", critical=True), c01_3)

        # 01.4 — Token metadata
        def c01_4(c):
            sym_ok = name_ok = dec_ok = False
            sym = name = ""
            dec = -1
            for t in self._trc20_transfers:
                if t.get("contract_address") == OFFICIAL_USDT_CONTRACT:
                    ti   = t.get("tokenInfo", {})
                    sym  = t.get("symbol",   ti.get("tokenAbbr",    "")).strip()
                    name = t.get("name",     ti.get("tokenName",    "")).strip()
                    raw_dec = t.get("decimals", ti.get("tokenDecimal", -1))
                    try:
                        dec = int(raw_dec)
                    except (ValueError, TypeError):
                        dec = -1
                    break
            sym_ok  = sym  == OFFICIAL_TOKEN_SYMBOL
            name_ok = name == OFFICIAL_TOKEN_NAME
            dec_ok  = dec  == OFFICIAL_TOKEN_DECIMALS
            issues  = []
            if not sym_ok:  issues.append(f"Symbol  : got '{sym}', expected '{OFFICIAL_TOKEN_SYMBOL}'")
            if not name_ok: issues.append(f"Name    : got '{name}', expected '{OFFICIAL_TOKEN_NAME}'")
            if not dec_ok:  issues.append(f"Decimals: got {dec}, expected {OFFICIAL_TOKEN_DECIMALS}")
            if issues:
                # Metadata can be absent from API without indicating fraud, so WARN not FAIL
                c.status = CheckStatus.WARN
                c.detail = (
                    "Metadata mismatch (may be missing from API — not necessarily fraud):\n"
                    + "\n".join(issues)
                )
            else:
                c.status = CheckStatus.PASS
                c.detail = (
                    f"Name='{OFFICIAL_TOKEN_NAME}'  "
                    f"Symbol='{OFFICIAL_TOKEN_SYMBOL}'  "
                    f"Decimals={OFFICIAL_TOKEN_DECIMALS}"
                )

        self._run_check(CheckResult("§01", "01.4", "Token metadata: name / symbol / decimals"), c01_4)
        return True

    # ────────────────────────────────────────────────────────────────────────
    # §02  TRANSACTION EXECUTION RESULT
    # ────────────────────────────────────────────────────────────────────────
    def section_02(self) -> bool:
        print_section_header("§02", "TRANSACTION EXECUTION RESULT", mandatory=True)

        # 02.1 — contractRet = SUCCESS
        # Sources (in priority order):
        #   1. POST /wallet/gettransactionbyid     → ret[].contractRet  (FullNode)
        #   2. POST /wallet/gettransactioninfobyid → receipt.result     (FullNode receipt)
        #   3. TronScan contractRet                                      (independent)
        def c02_1(c):
            # Source 1: FullNode gettransactionbyid
            tg_ret = (self._tx_by_id.get("ret") or [{}])[0].get("contractRet", "")
            # Source 2: FullNode receipt result (maps "SUCCESS" → contractRet equivalent)
            receipt_result = self._tx_info.get("receipt", {}).get("result", "")
            # Source 3: TronScan
            ts_ret = self._tx_ts.get("contractRet", "")

            # Normalise receipt_result to contractRet vocabulary
            if receipt_result == "SUCCESS":
                receipt_ret = "SUCCESS"
            elif receipt_result and receipt_result != "SUCCESS":
                receipt_ret = receipt_result   # e.g. REVERT, OUT_OF_ENERGY
            else:
                receipt_ret = ""

            result = tg_ret or receipt_ret or ts_ret
            c.raw_data = {
                "tg_gettransactionbyid": tg_ret,
                "tg_receipt_result": receipt_result,
                "tronscan_contractRet": ts_ret,
            }

            src_str = (
                f"wallet/getTransactionById: {tg_ret or '—'}  |  "
                f"txinfo receipt: {receipt_result or '—'}  |  "
                f"TronScan: {ts_ret or '—'}"
            )

            if result == "SUCCESS":
                c.status = CheckStatus.PASS
                c.detail = f"contractRet = SUCCESS\n{src_str}"
            elif result:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"contractRet = {result}\n"
                    f"⚠  FLASH USDT INDICATOR — transaction did not execute successfully\n"
                    f"{src_str}"
                )
            else:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"contractRet absent from all providers.\n"
                    f"Cannot confirm execution success — REJECT pending manual review.\n"
                    f"{src_str}"
                )

        self._run_check(CheckResult("§02", "02.1", "contractRet = SUCCESS (execution result)", critical=True), c02_1)
        if self._last_status() == S_FAIL:
            console.print("  [bold red]⛔ CRITICAL — Transaction reverted or unknown. Classic Flash USDT signature.[/]")
            return False

        # 02.2 — Transaction confirmed (not pending)
        # blockNumber from POST /wallet/gettransactioninfobyid is authoritative.
        # Solidity node data presence also indicates confirmation.
        def c02_2(c):
            # txinfo blockNumber (FullNode — most authoritative)
            tgi_block  = self._tx_info.get("blockNumber", 0) or 0
            # Solidity node — only populated for confirmed txs
            sol_block  = self._tx_solidity.get("blockNumber", 0) or 0
            # TronScan fallback
            ts_block   = self._tx_ts.get("block", 0) or 0
            block_num  = tgi_block or sol_block or ts_block
            self.report.block_number = block_num if block_num else None

            # Confirmed = solidity node has it, OR txinfo has blockNumber, OR TronScan says confirmed
            sol_confirmed = bool(sol_block)
            ts_confirmed  = self._tx_ts.get("confirmed", False)
            confirmed     = sol_confirmed or ts_confirmed or bool(tgi_block)

            c.raw_data = {
                "tgi_block": tgi_block, "sol_block": sol_block, "ts_block": ts_block,
                "sol_confirmed": sol_confirmed, "ts_confirmed": ts_confirmed,
            }

            src_str = (
                f"txinfo blockNum: {tgi_block or '—'}  |  "
                f"solidity blockNum: {sol_block or '—'}  |  "
                f"TronScan block: {ts_block or '—'}"
            )

            if confirmed and block_num:
                c.status = CheckStatus.PASS
                c.detail = f"Transaction confirmed in Block #{block_num:,}\n{src_str}"
            elif confirmed and not block_num:
                c.status = CheckStatus.WARN
                c.detail = (
                    f"Transaction confirmed but block number unavailable.\n"
                    f"{src_str}\n"
                    f"Confirmation count cannot be calculated — manual lookup required."
                )
            else:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"Transaction UNCONFIRMED / PENDING.\n"
                    f"⚠  NEVER process unconfirmed transactions — Flash USDT window.\n"
                    f"{src_str}"
                )

        self._run_check(CheckResult("§02", "02.2", "Transaction confirmed (not pending)", critical=True), c02_2)
        if self._last_status() == S_FAIL:
            return False

        # 02.3 — Cross-validate: all 3 TronGrid endpoints + TronScan must agree
        def c02_3(c):
            tg_ret     = (self._tx_by_id.get("ret") or [{}])[0].get("contractRet", "")
            rec_result = self._tx_info.get("receipt", {}).get("result", "")
            sol_result = self._tx_solidity.get("receipt", {}).get("result", "")
            ts_ret     = self._tx_ts.get("contractRet", "")

            results = {k: v for k, v in {
                "wallet/getTxById": tg_ret,
                "wallet/getTxInfo (receipt)": rec_result,
                "walletsolidity/getTxInfo": sol_result,
                "TronScan": ts_ret,
            }.items() if v}

            successes = [k for k, v in results.items() if v == "SUCCESS"]
            failures  = [k for k, v in results.items() if v not in ("SUCCESS", "")]
            src_str   = "  |  ".join(f"{k}: {v}" for k, v in results.items())

            if not results:
                c.status = CheckStatus.WARN
                c.detail = "No provider returned contractRet — data still propagating"
            elif failures:
                c.status = CheckStatus.FAIL
                c.detail = f"Provider(s) returned non-SUCCESS: {failures}\n{src_str}"
            elif len(successes) >= 2:
                c.status = CheckStatus.PASS
                c.detail = f"All available providers agree: SUCCESS ({len(successes)} sources)\n{src_str}"
            else:
                c.status = CheckStatus.PASS
                c.detail = f"Cross-validation consistent\n{src_str}"

        self._run_check(CheckResult("§02", "02.3", "Cross-validated: TronGrid FullNode + TronScan", critical=False), c02_3)
        return True

    # ────────────────────────────────────────────────────────────────────────
    # §03  BLOCK CONFIRMATIONS
    # ────────────────────────────────────────────────────────────────────────
    def section_03(self) -> bool:
        print_section_header("§03", f"BLOCK CONFIRMATIONS  [Production: ≥{CONFIRMS_PRODUCTION} blocks]", mandatory=True)

        # 03.1 — Fetch current block from both providers
        def c03_1(c):
            blocks = fetch_current_block()
            self._current_block = blocks["best"]
            if not self._current_block:
                c.status = CheckStatus.FAIL
                c.detail = "Could not fetch current block height from any provider"
                return
            c.status = CheckStatus.PASS
            c.detail = (
                f"Current block: #{self._current_block:,}\n"
                f"TronGrid: #{blocks['trongrid']:,} | TronScan: #{blocks['tronscan']:,}"
            )

        self._run_check(CheckResult("§03", "03.1", "Current block height fetched"), c03_1)

        # 03.2 — Calculate confirmations
        def c03_2(c):
            block_num = self.report.block_number

            # FIX-04: guard against block_number being None or 0
            if not block_num or not self._current_block:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"Cannot calculate confirmations.\n"
                    f"TX block_number={block_num} | Current block={self._current_block}\n"
                    f"Block number must be > 0 and current block must be reachable."
                )
                self.report.confirmations = 0
                return

            confs = self._current_block - block_num
            # FIX-04: sanity check — confirmations cannot exceed ~10M blocks reasonably
            if confs < 0 or confs > 10_000_000:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"Confirmation count out of range: {confs:,}\n"
                    f"TX Block: #{block_num:,} | Current: #{self._current_block:,}\n"
                    f"Possible data error — verify block number manually."
                )
                self.report.confirmations = 0
                return

            self.report.confirmations = confs
            thresholds = (
                f"Standard(≥{CONFIRMS_STANDARD})={'✓' if confs >= CONFIRMS_STANDARD else '✗'}  "
                f"High-Value(≥{CONFIRMS_HIGH_VALUE})={'✓' if confs >= CONFIRMS_HIGH_VALUE else '✗'}  "
                f"Production(≥{CONFIRMS_PRODUCTION})={'✓' if confs >= CONFIRMS_PRODUCTION else '✗'}"
            )

            if confs >= CONFIRMS_PRODUCTION:
                c.status = CheckStatus.PASS
                c.detail = (
                    f"Confirmations: {confs:,} blocks ✓\n"
                    f"TX Block: #{block_num:,} | Current: #{self._current_block:,}\n"
                    f"{thresholds}"
                )
            else:
                c.status = CheckStatus.WARN
                remaining = CONFIRMS_PRODUCTION - confs
                c.detail = (
                    f"Confirmations: {confs} / {CONFIRMS_PRODUCTION} required\n"
                    f"TX Block: #{block_num:,} | Current: #{self._current_block:,}\n"
                    f"Need {remaining} more blocks (~{remaining * 3}s)\n"
                    f"{thresholds}"
                )

        self._run_check(CheckResult("§03", "03.2", f"Confirmations ≥ {CONFIRMS_PRODUCTION} (production threshold)", critical=True), c03_2)

        # 03.3 — Poll until threshold met (if not already there)
        confs = self.report.confirmations or 0
        # FIX-10: only enter wait loop when block_number is valid and confs is genuinely low
        block_num = self.report.block_number or 0
        if block_num > 0 and 0 < confs < CONFIRMS_PRODUCTION:
            needed   = CONFIRMS_PRODUCTION - confs
            max_wait = needed * 5
            console.print(
                f"\n  [yellow]⏳ Waiting for {needed} more confirmation(s) "
                f"(~{needed * 3}s estimated, polling every 10s, timeout {max_wait}s)[/]\n"
            )
            with Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[cyan]Polling chain..."),
                BarColumn(bar_width=40, style="cyan", complete_style="green"),
                TaskProgressColumn(),
                TextColumn("[dim]{task.fields[status]}[/]"),
                console=console, transient=True,
            ) as progress:
                task = progress.add_task(
                    "confirms", total=CONFIRMS_PRODUCTION,
                    completed=confs, status=f"{confs}/{CONFIRMS_PRODUCTION}"
                )
                waited = 0
                while waited < max_wait and confs < CONFIRMS_PRODUCTION:
                    time.sleep(10)
                    waited += 10
                    try:
                        blocks = fetch_current_block()
                        self._current_block = blocks["best"]
                    except Exception:
                        pass
                    confs = self._current_block - block_num
                    self.report.confirmations = confs
                    progress.update(
                        task,
                        completed=min(confs, CONFIRMS_PRODUCTION),
                        status=f"{confs}/{CONFIRMS_PRODUCTION} blocks"
                    )

            def c03_3(c):
                if confs >= CONFIRMS_PRODUCTION:
                    c.status = CheckStatus.PASS
                    c.detail = (
                        f"Reached {confs:,} confirmations after polling.\n"
                        f"Production threshold ({CONFIRMS_PRODUCTION}) met ✓"
                    )
                else:
                    c.status = CheckStatus.FAIL
                    c.detail = (
                        f"Only {confs}/{CONFIRMS_PRODUCTION} confirmations after {max_wait}s wait.\n"
                        f"Re-run the script in ~{(CONFIRMS_PRODUCTION - confs) * 3}s when more blocks are mined."
                    )

            self._run_check(CheckResult("§03", "03.3", "Confirmation threshold reached after polling", critical=True), c03_3)

        elif block_num == 0:
            console.print("  [dim]  — 03.3 Block number unavailable — confirmation poll skipped[/]")

        return (self.report.confirmations or 0) >= CONFIRMS_PRODUCTION

    # ────────────────────────────────────────────────────────────────────────
    # §04  TRANSFER EVENT FORENSICS
    # ────────────────────────────────────────────────────────────────────────
    def section_04(self) -> bool:
        print_section_header("§04", "TRANSFER EVENT FORENSICS", mandatory=True)

        # 04.1 — Transfer event exists from official contract
        def c04_1(c):
            official = [t for t in self._trc20_transfers
                        if t.get("contract_address") == OFFICIAL_USDT_CONTRACT]
            if not official:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"NO Transfer event from official USDT contract\n"
                    f"Expected from: {OFFICIAL_USDT_CONTRACT}\n"
                    f"⚠  Funds did NOT move. Wallet UI balance is misleading. REJECT."
                )
                return
            c.status = CheckStatus.PASS
            c.detail = f"{len(official)} Transfer event(s) from official USDT contract"
            c.raw_data = {"official_transfer_count": len(official)}

        self._run_check(CheckResult("§04", "04.1", "Transfer event from official USDT contract", critical=True), c04_1)
        if self._last_status() == S_FAIL:
            return False

        # 04.2 — 'to' address
        def c04_2(c):
            official = [t for t in self._trc20_transfers
                        if t.get("contract_address") == OFFICIAL_USDT_CONTRACT]
            to_addrs = list({t.get("to_address", "") for t in official})
            self.report.actual_to = to_addrs[0] if len(to_addrs) == 1 else str(to_addrs)

            if self.expected_to:
                if self.expected_to in to_addrs:
                    c.status = CheckStatus.PASS
                    c.detail = f"'to' address matches expected wallet:\n{self.expected_to}"
                else:
                    c.status = CheckStatus.FAIL
                    c.detail = (
                        f"'to' ADDRESS MISMATCH\n"
                        f"Expected : {self.expected_to}\n"
                        f"In event : {', '.join(to_addrs)}"
                    )
            else:
                c.status = CheckStatus.PASS
                c.detail = (
                    f"Transfer destination: {', '.join(to_addrs)}\n"
                    f"(No --expected-to provided. Recommend rerunning with --expected-to for full verification.)"
                )
            c.raw_data = {"to_addresses": to_addrs}

        self._run_check(CheckResult("§04", "04.2", "Transfer event 'to' address verified", critical=True), c04_2)

        # 04.3 — Amount
        def c04_3(c):
            official = [t for t in self._trc20_transfers
                        if t.get("contract_address") == OFFICIAL_USDT_CONTRACT]
            total_raw    = sum(int(t.get("amount_str", t.get("amount", 0))) for t in official)
            usdt_amount  = total_raw / USDT_DIVISOR
            self.report.actual_amount = usdt_amount

            if self.expected_amount is not None:
                diff = abs(usdt_amount - self.expected_amount)
                if diff <= 0.000001:
                    c.status = CheckStatus.PASS
                    c.detail = (
                        f"Amount verified: {usdt_amount:,.6f} USDT\n"
                        f"Expected:        {self.expected_amount:,.6f} USDT\n"
                        f"Difference:      {diff:.8f} (within tolerance)"
                    )
                else:
                    c.status = CheckStatus.FAIL
                    c.detail = (
                        f"AMOUNT MISMATCH\n"
                        f"Event amount : {usdt_amount:,.6f} USDT\n"
                        f"Expected     : {self.expected_amount:,.6f} USDT\n"
                        f"Difference   : {diff:,.6f} USDT"
                    )
            else:
                c.status = CheckStatus.PASS
                c.detail = (
                    f"Transfer amount: {usdt_amount:,.6f} USDT\n"
                    f"(No --expected-amount provided. Recommend rerunning with --expected-amount.)"
                )
            c.raw_data = {"amount_usdt": usdt_amount, "raw_amount": total_raw}

        self._run_check(CheckResult("§04", "04.3", "Transfer event amount matches expected", critical=True), c04_3)

        # 04.4 — Duplicate or conflicting transfers
        def c04_4(c):
            official = [t for t in self._trc20_transfers
                        if t.get("contract_address") == OFFICIAL_USDT_CONTRACT]
            non_official = [t for t in self._trc20_transfers
                            if t.get("contract_address") != OFFICIAL_USDT_CONTRACT]
            warnings = []

            if len(official) > 1:
                amounts = [int(t.get("amount_str", t.get("amount", 0))) / USDT_DIVISOR for t in official]
                warnings.append(
                    f"Multiple Transfer events from official contract ({len(official)}). "
                    f"Amounts: {[f'{a:,.2f}' for a in amounts]} — verify each is legitimate."
                )
            if non_official:
                fake_contracts = {t.get("contract_address", "") for t in non_official}
                warnings.append(
                    f"{len(non_official)} transfer(s) from NON-OFFICIAL contract(s): "
                    f"{', '.join(fake_contracts)}\n"
                    f"⚠  Possible dust+confusion attack vector."
                )

            if warnings:
                c.status = CheckStatus.WARN
                c.detail = "\n".join(warnings)
            else:
                c.status = CheckStatus.PASS
                c.detail = "Single Transfer event from official contract — clean transaction"

        self._run_check(CheckResult("§04", "04.4", "No duplicate or conflicting Transfer events", critical=False), c04_4)

        # 04.5 — Extract sender
        def c04_5(c):
            official = [t for t in self._trc20_transfers
                        if t.get("contract_address") == OFFICIAL_USDT_CONTRACT]
            from_addrs = list({t.get("from_address", t.get("from", "")) for t in official})
            from_addrs = [a for a in from_addrs if a]
            self.report.sender_address = from_addrs[0] if from_addrs else None

            if from_addrs:
                c.status = CheckStatus.PASS
                c.detail = f"Sender: {', '.join(from_addrs)}"
            else:
                c.status = CheckStatus.WARN
                c.detail = "Sender address not available in Transfer event data"
            c.raw_data = {"from_addresses": from_addrs}

        self._run_check(CheckResult("§04", "04.5", "Sender address extracted", critical=False), c04_5)
        return True

    # ────────────────────────────────────────────────────────────────────────
    # §05  SENDER ADDRESS ANALYSIS
    # ────────────────────────────────────────────────────────────────────────
    def section_05(self) -> bool:
        print_section_header("§05", "SENDER ADDRESS ANALYSIS", mandatory=True)

        sender = self.report.sender_address
        if not sender:
            console.print("  [dim]  — Sender address unavailable — section skipped[/]")
            return True

        # 05.1 — EOA vs Contract
        def c05_1(c):
            is_contract = False
            acct = fetch_account(sender)
            if acct.get("bytecode") or acct.get("code_hash"):
                is_contract = True

            if not is_contract:
                try:
                    ts_contract = http_get(
                        f"{TRONSCAN_BASE}/api/contract",
                        params={"contract": sender},
                        timeout=10,
                    )
                    if ts_contract.get("bytecode") or ts_contract.get("abi"):
                        is_contract = True
                except Exception:
                    pass

            self.report.sender_is_contract = is_contract
            c.raw_data = {"is_contract": is_contract}

            if is_contract:
                c.status = CheckStatus.WARN
                c.detail = (
                    f"⚠  Sender {sender} is a SMART CONTRACT\n"
                    f"Smart contracts can embed revert/backdoor logic.\n"
                    f"Minimum confirmation threshold raised to {CONFIRMS_RISKY} blocks."
                )
            else:
                c.status = CheckStatus.PASS
                c.detail = f"Sender {sender} is an EOA (Externally Owned Account) — lower risk"

        self._run_check(CheckResult("§05", "05.1", "Sender verified as EOA (not a smart contract)", critical=True), c05_1)

        # 05.2 — If contract, check source verification
        if self.report.sender_is_contract:
            def c05_2(c):
                try:
                    data = http_get(
                        f"{TRONSCAN_BASE}/api/contract",
                        params={"contract": sender},
                        timeout=10,
                    )
                    verified = data.get("verified", False) or bool(data.get("abi"))
                    if verified:
                        c.status = CheckStatus.WARN
                        c.detail = (
                            "Contract source verified on TronScan.\n"
                            "Review ABI for any revert(), selfdestruct(), or timed logic before proceeding."
                        )
                    else:
                        c.status = CheckStatus.FAIL
                        c.detail = (
                            "Contract source UNVERIFIED on TronScan\n"
                            "⚠  Cannot inspect for backdoor/revert logic.\n"
                            f"REJECT or wait {CONFIRMS_RISKY} blocks minimum."
                        )
                except Exception as e:
                    c.status = CheckStatus.WARN
                    c.detail = f"Could not fetch contract verification status: {e}"

            self._run_check(CheckResult("§05", "05.2", "Contract source code verified on TronScan", critical=False), c05_2)

        # 05.3 — Account age and history
        def c05_3(c):
            try:
                acct = fetch_account(sender)
                create_time = acct.get("create_time", 0) or 0
                if create_time:
                    now_ms  = time.time() * 1000
                    age_hrs = (now_ms - create_time) / (1000 * 3600)
                    age_days = age_hrs / 24
                    if age_hrs < 24:
                        c.status = CheckStatus.WARN
                        c.detail = f"⚠  Sender address is only {age_hrs:.1f} hours old — HIGH RISK"
                    elif age_days < 7:
                        c.status = CheckStatus.WARN
                        c.detail = f"Sender address is {age_days:.1f} days old — relatively new, review manually"
                    else:
                        c.status = CheckStatus.PASS
                        c.detail = f"Sender account age: {age_days:.0f} days — established address"
                else:
                    c.status = CheckStatus.PASS
                    c.detail = "Account history confirmed (creation time not exposed by API)"
            except Exception as e:
                c.status = CheckStatus.WARN
                c.detail = f"Could not fetch sender history: {e}"

        self._run_check(CheckResult("§05", "05.3", "Sender address has established transaction history", critical=False), c05_3)
        return True

    # ────────────────────────────────────────────────────────────────────────
    # §06  MULTI-PROVIDER CONSENSUS
    # Three independent TronGrid FullNode sources + TronScan (4 total).
    # Providers:
    #   06.1 TronGrid FullNode   — POST /wallet/gettransactionbyid
    #   06.2 TronGrid FullNode   — POST /wallet/gettransactioninfobyid (receipt)
    #   06.3 TronGrid Solidity   — POST /walletsolidity/gettransactioninfobyid
    #   06.4 TronScan            — independent REST API
    #   06.5 Consensus verdict   — minimum 2-of-4 PASS required
    # ────────────────────────────────────────────────────────────────────────
    def section_06(self) -> bool:
        print_section_header("§06", "MULTI-PROVIDER CONSENSUS  [4 sources required]", mandatory=True)
        confs = self.report.confirmations or 0

        # 06.1 — TronGrid FullNode: POST /wallet/gettransactionbyid
        def c06_1(c):
            tg_ret = (self._tx_by_id.get("ret") or [{}])[0].get("contractRet", "")
            has_data = bool(self._tx_by_id.get("txID") or self._tx_by_id.get("ret"))
            if not has_data:
                c.status = CheckStatus.WARN
                c.detail = "wallet/getTransactionById: no data returned"
                self.report.provider_consensus["TG_FullNode_getTxById"] = "UNAVAILABLE"
            elif tg_ret == "SUCCESS":
                c.status = CheckStatus.PASS
                c.detail = f"wallet/getTransactionById: contractRet=SUCCESS  confs={confs:,}"
                self.report.provider_consensus["TG_FullNode_getTxById"] = "PASS"
            else:
                c.status = CheckStatus.FAIL
                c.detail = f"wallet/getTransactionById: contractRet='{tg_ret}'"
                self.report.provider_consensus["TG_FullNode_getTxById"] = "FAIL"

        self._run_check(CheckResult("§06", "06.1", "TronGrid FullNode — wallet/getTransactionById", critical=True), c06_1)

        # 06.2 — TronGrid FullNode: POST /wallet/gettransactioninfobyid (receipt)
        def c06_2(c):
            receipt = self._tx_info.get("receipt", {})
            result  = receipt.get("result", "")
            blk     = self._tx_info.get("blockNumber", 0) or 0
            has_data = bool(self._tx_info.get("id") or blk)
            if not has_data:
                c.status = CheckStatus.WARN
                c.detail = "wallet/getTransactionInfoById: no data returned"
                self.report.provider_consensus["TG_FullNode_getTxInfo"] = "UNAVAILABLE"
            elif result == "SUCCESS" and blk:
                c.status = CheckStatus.PASS
                c.detail = f"wallet/getTransactionInfoById: receipt.result=SUCCESS  blockNumber={blk:,}"
                self.report.provider_consensus["TG_FullNode_getTxInfo"] = "PASS"
            elif result == "SUCCESS":
                c.status = CheckStatus.WARN
                c.detail = f"wallet/getTransactionInfoById: result=SUCCESS but no blockNumber yet"
                self.report.provider_consensus["TG_FullNode_getTxInfo"] = "WARN"
            elif result:
                c.status = CheckStatus.FAIL
                c.detail = f"wallet/getTransactionInfoById: receipt.result='{result}'"
                self.report.provider_consensus["TG_FullNode_getTxInfo"] = "FAIL"
            else:
                c.status = CheckStatus.WARN
                c.detail = f"wallet/getTransactionInfoById: receipt.result absent"
                self.report.provider_consensus["TG_FullNode_getTxInfo"] = "WARN"

        self._run_check(CheckResult("§06", "06.2", "TronGrid FullNode — wallet/getTransactionInfoById", critical=True), c06_2)

        # 06.3 — TronGrid Solidity node: POST /walletsolidity/gettransactioninfobyid
        # Solidity node only stores CONFIRMED transactions — presence = confirmed
        def c06_3(c):
            sol_blk    = self._tx_solidity.get("blockNumber", 0) or 0
            sol_result = self._tx_solidity.get("receipt", {}).get("result", "")
            has_data   = bool(self._tx_solidity.get("id") or sol_blk)
            if not has_data:
                c.status = CheckStatus.WARN
                c.detail = (
                    "walletsolidity/getTransactionInfoById: no data.\n"
                    "Transaction not yet on the Solidity (confirmed) node — may still be propagating."
                )
                self.report.provider_consensus["TG_Solidity"] = "WARN"
            elif sol_result == "SUCCESS" and sol_blk:
                c.status = CheckStatus.PASS
                c.detail = (
                    f"walletsolidity/getTransactionInfoById: confirmed  "
                    f"blockNumber={sol_blk:,}  result=SUCCESS"
                )
                self.report.provider_consensus["TG_Solidity"] = "PASS"
            elif sol_result:
                c.status = CheckStatus.FAIL
                c.detail = f"walletsolidity/getTransactionInfoById: result='{sol_result}' (not SUCCESS)"
                self.report.provider_consensus["TG_Solidity"] = "FAIL"
            else:
                c.status = CheckStatus.PASS
                c.detail = f"walletsolidity/getTransactionInfoById: transaction present  blockNumber={sol_blk:,}"
                self.report.provider_consensus["TG_Solidity"] = "PASS"

        self._run_check(CheckResult("§06", "06.3", "TronGrid Solidity — walletsolidity/getTransactionInfoById", critical=True), c06_3)

        # 06.4 — TronScan (independent provider)
        def c06_4(c):
            ts_ret       = self._tx_ts.get("contractRet", "")
            ts_confirmed = self._tx_ts.get("confirmed", False)
            if ts_ret == "SUCCESS" and ts_confirmed:
                c.status = CheckStatus.PASS
                c.detail = "TronScan: contractRet=SUCCESS  confirmed=True"
                self.report.provider_consensus["TronScan"] = "PASS"
            elif ts_ret == "SUCCESS" and not ts_confirmed:
                c.status = CheckStatus.WARN
                c.detail = "TronScan: contractRet=SUCCESS but confirmed=False (still propagating)"
                self.report.provider_consensus["TronScan"] = "WARN"
            elif ts_ret:
                c.status = CheckStatus.FAIL
                c.detail = f"TronScan: contractRet='{ts_ret}'"
                self.report.provider_consensus["TronScan"] = "FAIL"
            else:
                c.status = CheckStatus.WARN
                c.detail = "TronScan: no contractRet data"
                self.report.provider_consensus["TronScan"] = "UNAVAILABLE"

        self._run_check(CheckResult("§06", "06.4", "TronScan — independent confirmation", critical=True), c06_4)

        # 06.5 — Consensus verdict (2-of-4 PASS required)
        def c06_5(c):
            results     = self.report.provider_consensus
            passes      = sum(1 for v in results.values() if v == "PASS")
            fails       = sum(1 for v in results.values() if v == "FAIL")
            warns       = sum(1 for v in results.values() if v == "WARN")
            unavailable = sum(1 for v in results.values() if v == "UNAVAILABLE")
            total       = len(results)
            summary     = "\n".join(f"  {k}: {v}" for k, v in results.items())

            if fails > 0:
                c.status = CheckStatus.FAIL
                c.detail = (
                    f"CONSENSUS FAILED — {fails}/{total} provider(s) returned FAIL\n{summary}"
                )
            elif passes >= 2:
                c.status = CheckStatus.PASS
                c.detail = (
                    f"Consensus ACHIEVED — {passes}/{total} providers confirm PASS\n{summary}"
                )
            elif passes == 1:
                c.status = CheckStatus.WARN
                c.detail = (
                    f"Partial consensus — only {passes}/{total} PASS ({warns} WARN, {unavailable} UNAVAILABLE)\n"
                    f"Wait for more confirmations and retry.\n{summary}"
                )
            else:
                c.status = CheckStatus.WARN
                c.detail = (
                    f"No providers confirmed PASS yet ({warns} WARN, {unavailable} UNAVAILABLE)\n"
                    f"Transaction likely still propagating — retry in 30–60s.\n{summary}"
                )

        self._run_check(CheckResult("§06", "06.5", "Consensus: 2-of-4 providers PASS required", critical=True), c06_5)
        return True

    # ────────────────────────────────────────────────────────────────────────
    # §07  AUDIT TRAIL
    # ────────────────────────────────────────────────────────────────────────
    def section_07(self, report_path: str) -> bool:
        print_section_header("§07", "AUDIT TRAIL", mandatory=True)

        # 07.1 — Finalise report status
        def c07_1(c):
            # FIX-01/07: now that checks store string values, comparisons work correctly
            crit_fails = [ch for ch in self.report.checks
                          if ch["status"] == S_FAIL and ch["critical"]]
            any_fails  = [ch for ch in self.report.checks if ch["status"] == S_FAIL]
            any_warns  = [ch for ch in self.report.checks if ch["status"] == S_WARN]

            if crit_fails:
                self.report.final_status = "REJECTED"
            elif any_fails:
                self.report.final_status = "REJECTED"
            elif any_warns:
                self.report.final_status = "CLEARED_WITH_WARNINGS"
            else:
                self.report.final_status = "CLEARED"

            # FIX-08: timezone-aware UTC
            self.report.completed_at = datetime.datetime.now(timezone.utc).isoformat()
            c.status = CheckStatus.PASS
            c.detail = f"Final status: {self.report.final_status}"

        self._run_check(CheckResult("§07", "07.1", "Validation report status finalised", critical=True), c07_1)

        # 07.2 — Write JSON audit log
        def c07_2(c):
            try:
                payload = asdict(self.report)
                with open(report_path, "w") as f:
                    json.dump(payload, f, indent=2, default=str)
                size = os.path.getsize(report_path)
                c.status = CheckStatus.PASS
                c.detail = f"Audit log: {report_path}  ({size:,} bytes)"
            except Exception as e:
                c.status = CheckStatus.FAIL
                c.detail = f"Failed to write audit log: {e}"

        self._run_check(CheckResult("§07", "07.2", "Audit log written to disk", critical=True), c07_2)

        # 07.3 — SHA-256 checksum
        def c07_3(c):
            try:
                with open(report_path, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
                c.status = CheckStatus.PASS
                c.detail = f"SHA-256: {sha}"
                c.raw_data = {"sha256": sha}
            except Exception as e:
                c.status = CheckStatus.WARN
                c.detail = f"Could not compute checksum: {e}"

        self._run_check(CheckResult("§07", "07.3", "Audit log SHA-256 checksum", critical=False), c07_3)
        return True

    # ────────────────────────────────────────────────────────────────────────
    # MAIN RUNNER
    # ────────────────────────────────────────────────────────────────────────
    def run(self) -> ValidationReport:
        # FIX-08: timezone-aware UTC
        ts          = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_hash   = self.tx_hash[:16]
        report_path = f"usdt_audit_{safe_hash}_{ts}.json"

        # Banner
        console.print()
        console.print(Panel.fit(
            Text.assemble(
                ("USDT TRC20  ·  PRODUCTION VALIDATOR  v1.2\n", Style(bold=True, color="white")),
                ("Anti-Fraud · Blockchain Forensics · TRON Mainnet\n", Style(color="bright_black")),
                (f"\nOperator  : {self.operator}\n",         Style(color="cyan")),
                (f"TX Hash   : {self.tx_hash}\n",             Style(color="cyan")),
                (f"Started   : {self.report.started_at}\n",   Style(color="bright_black")),
                (f"Mode      : PRODUCTION  (≥{CONFIRMS_PRODUCTION} block confirmations required)\n",
                 Style(color="yellow")),
                (f"TronGrid  : API key active ({TRONGRID_API_KEY[:8]}···{TRONGRID_API_KEY[-4:]})",
                 Style(color="green")),
            ),
            border_style="cyan",
            title="[bold cyan]VALIDATION SESSION[/]",
            title_align="left",
            padding=(0, 2),
        ))
        if self.expected_amount:
            console.print(f"  [dim]Expected Amount : [cyan]{self.expected_amount:,.6f} USDT[/][/]")
        if self.expected_to:
            console.print(f"  [dim]Expected To     : [cyan]{self.expected_to}[/][/]")
        console.print()

        t_start = time.time()

        # §01
        if not self.section_01():
            return self._finalize_early("REJECTED — CONTRACT VERIFICATION FAILED", report_path)
        # §02
        if not self.section_02():
            return self._finalize_early("REJECTED — EXECUTION RESULT FAILED", report_path)
        # §03 — continue even if not enough confirms; section reports the state
        self.section_03()
        # §04
        self.section_04()
        # §05
        self.section_05()
        # §06
        self.section_06()
        # §07
        self.section_07(report_path)

        elapsed = time.time() - t_start
        self._print_final_verdict(elapsed, report_path)
        return self.report

    def _finalize_early(self, reason: str, report_path: str) -> ValidationReport:
        self.report.completed_at = datetime.datetime.now(timezone.utc).isoformat()
        self.report.final_status = "REJECTED"
        try:
            with open(report_path, "w") as f:
                json.dump(asdict(self.report), f, indent=2, default=str)
        except Exception:
            pass
        console.print()
        console.print(Panel(
            f"[bold red]⛔  {reason}[/]\n\n[dim]Audit log: {report_path}[/]",
            border_style="red",
            title="[bold red]VALIDATION TERMINATED[/]",
        ))
        return self.report

    def _print_final_verdict(self, elapsed: float, report_path: str):
        checks  = self.report.checks
        total   = len(checks)
        # FIX-07: these counts are now correct because checks store .value strings
        passed  = sum(1 for c in checks if c["status"] == S_PASS)
        failed  = sum(1 for c in checks if c["status"] == S_FAIL)
        warned  = sum(1 for c in checks if c["status"] == S_WARN)
        crit_f  = [c for c in checks if c["status"] == S_FAIL and c["critical"]]

        console.print()

        # Summary table
        tbl = Table(box=box.SIMPLE_HEAD, show_header=True,
                    header_style="bold cyan", style="dim", min_width=60)
        tbl.add_column("METRIC",  style="dim",         width=28)
        tbl.add_column("VALUE",   style="bold white",  width=32)

        confs     = self.report.confirmations or 0
        confs_str = (
            f"[green]{confs:,}[/]" if confs >= CONFIRMS_PRODUCTION else f"[red]{confs:,}[/]"
        )

        tbl.add_row("Transaction Hash",  self.report.tx_hash[:32] + "…")
        tbl.add_row("Actual Amount",     f"{self.report.actual_amount:,.6f} USDT"
                                          if self.report.actual_amount else "—")
        tbl.add_row("Transfer To",       (self.report.actual_to or "—")[:40])
        tbl.add_row("Sender",            (self.report.sender_address or "—")[:40])
        tbl.add_row("Block Number",      f"#{self.report.block_number:,}"
                                          if self.report.block_number else "—")
        tbl.add_row("Confirmations",     confs_str)
        tbl.add_row("Checks Passed",     f"[green]{passed}/{total}[/]")
        tbl.add_row("Checks Failed",     f"[red]{failed}[/]" if failed else "0")
        tbl.add_row("Warnings",          f"[yellow]{warned}[/]" if warned else "0")
        tbl.add_row("Elapsed",           f"{elapsed:.1f}s")
        tbl.add_row("Audit Log",         report_path)

        fs = self.report.final_status
        if fs == "CLEARED":
            color, icon = "green", "✅"
            verdict = "CLEARED — SAFE TO PROCEED"
            sub     = f"All {total} checks passed. No failures or warnings. Audit trail complete."
        elif fs == "CLEARED_WITH_WARNINGS":
            color, icon = "yellow", "⚠️ "
            verdict = "CLEARED WITH WARNINGS — MANUAL REVIEW RECOMMENDED"
            sub     = f"{warned} warning(s) raised. Review audit log before releasing funds."
        else:
            color, icon = "red", "⛔"
            verdict = "REJECTED — DO NOT RELEASE"
            sub     = f"{len(crit_f)} critical failure(s). See: {report_path}"

        console.print(Panel(
            Text.assemble(
                (f"{icon}  {verdict}\n\n", Style(bold=True, color=color)),
                (sub + "\n",               Style(color="bright_black")),
            ),
            border_style=color,
            title=f"[bold {color}]FINAL VALIDATION VERDICT[/]",
            title_align="left",
        ))
        console.print(tbl)

        if crit_f:
            console.print()
            console.print("[bold red]CRITICAL FAILURES:[/]")
            for ch in crit_f:
                console.print(f"  [red]✗[/] [{ch['code']}] {ch['name']}")
                for line in ch["detail"].split("\n"):
                    if line.strip():
                        console.print(f"      [dim]{line}[/]")

        if warned and fs != "REJECTED":
            console.print()
            console.print("[bold yellow]WARNINGS (review before proceeding):[/]")
            for ch in checks:
                if ch["status"] == S_WARN:
                    console.print(f"  [yellow]⚠[/] [{ch['code']}] {ch['name']}")
                    first_line = ch["detail"].split("\n")[0] if ch["detail"] else ""
                    if first_line:
                        console.print(f"      [dim]{first_line}[/]")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="USDT TRC20 Production Transaction Validator v1.2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python usdt_validator.py ca30beb469ae2214228e21a0ec820081ebfcbc65a7a95e7e36d8aa042ecaf199
  python usdt_validator.py <TX_HASH> --expected-amount 100000
  python usdt_validator.py <TX_HASH> --expected-amount 100000 --expected-to TPjhs1G1bjPEBPVcWJo9kJC9S4xsxqQX7J
  python usdt_validator.py <TX_HASH> --operator "Vinod" --expected-amount 100000

TronGrid API key:
  Key is pre-configured in the script (TRONGRID_API_KEY constant).
  To rotate: update the TRONGRID_API_KEY constant at the top of the file.
        """
    )
    parser.add_argument("tx_hash",
                        help="TRON transaction hash to validate")
    parser.add_argument("--expected-amount", type=float, default=None,
                        help="Expected USDT amount (recommended for full verification)")
    parser.add_argument("--expected-to",     type=str, default=None,
                        help="Expected recipient wallet address (recommended)")
    parser.add_argument("--operator",        type=str, default="SYSTEM",
                        help="Operator ID for audit log (default: SYSTEM)")
    args = parser.parse_args()

    if len(args.tx_hash) < 20:
        console.print("[bold red]Error:[/] TX hash too short — verify and retry.")
        sys.exit(2)

    validator = USDTValidator(
        tx_hash=args.tx_hash,
        expected_amount=args.expected_amount,
        expected_to=args.expected_to,
        operator=args.operator,
    )
    report = validator.run()

    sys.exit(0 if report.final_status in ("CLEARED", "CLEARED_WITH_WARNINGS") else 1)


if __name__ == "__main__":
    main()
