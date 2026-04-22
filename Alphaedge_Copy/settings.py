"""
AlphaCopy - Copy Trading Framework Configuration
Supports: Hyperliquid | Binance Futures | Polymarket
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Base bot configuration"""
    enabled: bool = True
    allocated_capital_usd: float = 10_000.0
    max_position_pct: float = 0.15          # Max 15% per position
    max_drawdown_pct: float = 0.20          # Stop bot if -20% drawdown
    max_open_positions: int = 5
    copy_ratio: float = 0.10               # Copy 10% of trader's size
    min_copy_size_usd: float = 50.0
    max_copy_size_usd: float = 2_000.0
    slippage_tolerance_pct: float = 0.005  # 0.5%
    dry_run: bool = True                   # ALWAYS start in dry-run!
    polling_interval_sec: int = 5


@dataclass
class HyperliquidConfig(BotConfig):
    # ── Auth ──────────────────────────────────────────────────────────────
    account_address: str = field(default_factory=lambda: os.getenv("HL_ACCOUNT_ADDRESS", ""))
    private_key: str     = field(default_factory=lambda: os.getenv("HL_PRIVATE_KEY", ""))
    api_url: str         = "https://api.hyperliquid.xyz"
    testnet_url: str     = "https://api.hyperliquid-testnet.xyz"
    use_testnet: bool    = True   # Flip to False for mainnet

    # ── Trader Selection ──────────────────────────────────────────────────
    target_wallets: list = field(default_factory=list)  # Paste from leaderboard
    leaderboard_min_pnl_30d: float   = 50_000.0  # Only copy wallets > $50k 30d PnL
    leaderboard_min_roi_30d: float   = 0.30       # > 30% ROI
    leaderboard_max_drawdown: float  = 0.25       # < 25% max DD

    # ── Position Management ───────────────────────────────────────────────
    default_leverage: int      = 3
    max_leverage: int          = 10
    stop_loss_pct: float       = 0.05   # 5% SL from entry
    take_profit_pct: float     = 0.15   # 15% TP
    trailing_stop_pct: float   = 0.03   # 3% trailing stop
    close_on_trader_close: bool = True


@dataclass
class BinanceConfig(BotConfig):
    # ── Auth ──────────────────────────────────────────────────────────────
    api_key: str    = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    testnet: bool   = True

    # ── Trader Selection ──────────────────────────────────────────────────
    target_encrypted_uids: list = field(default_factory=list)
    leaderboard_period: str  = "MONTHLY"   # DAILY | WEEKLY | MONTHLY | ALL
    leaderboard_sort_by: str = "PNL"       # ROI | PNL
    leaderboard_top_n: int   = 10          # Scan top N from leaderboard

    # ── Copy Trading Mode ─────────────────────────────────────────────────
    copy_mode: str = "FIXED_RATIO"   # FIXED_AMOUNT | FIXED_RATIO
    position_side: str = "BOTH"      # LONG | SHORT | BOTH

    # ── Position Management ───────────────────────────────────────────────
    default_leverage: int     = 3
    max_leverage: int         = 10
    stop_loss_pct: float      = 0.05
    take_profit_pct: float    = 0.15
    trailing_stop_pct: float  = 0.03
    max_portfolio_count: int  = 20  # Binance max is 20 portfolios

    # ── Endpoints (unofficial leaderboard scrape) ─────────────────────────
    leaderboard_base: str  = "https://www.binance.com/bapi/futures/v3/public/future/leaderboard"
    position_endpoint: str = "https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition"


@dataclass
class PolymarketConfig(BotConfig):
    # ── Auth ──────────────────────────────────────────────────────────────
    private_key: str = field(default_factory=lambda: os.getenv("POLY_PRIVATE_KEY", ""))
    funder_address: str = field(default_factory=lambda: os.getenv("POLY_FUNDER_ADDRESS", ""))
    clob_host: str   = "https://clob.polymarket.com"
    gamma_host: str  = "https://gamma-api.polymarket.com"
    chain_id: int    = 137   # Polygon mainnet

    # ── Trader Selection ──────────────────────────────────────────────────
    target_wallets: list = field(default_factory=list)
    min_pnl_usd: float   = 50_000.0
    min_win_rate: float  = 0.55
    min_trades: int      = 50
    max_position_age_days: int = 30  # Ignore old positions

    # ── Copy Strategy ─────────────────────────────────────────────────────
    # Prediction markets have NO leverage and NO stop-losses like perps.
    # Risk is inherently capped at position size (binary 0 or 1 outcome).
    min_price: float        = 0.05   # Don't buy at < 5¢ (lottery tickets)
    max_price: float        = 0.90   # Don't buy at > 90¢ (low upside)
    min_whale_size_usd: float = 5_000.0  # Only copy trades > $5k from whale
    consensus_threshold: int  = 2    # Enter only if 2+ whales agree
    max_market_exposure_pct: float = 0.10  # Max 10% of capital per market

    # ── Exit Rules ────────────────────────────────────────────────────────
    exit_on_whale_exit: bool = True
    profit_target_multiplier: float = 2.5  # Exit at 2.5x
    max_loss_pct: float = 0.50             # Exit if down 50% on position


@dataclass
class GlobalConfig:
    hyperliquid: HyperliquidConfig = field(default_factory=HyperliquidConfig)
    binance: BinanceConfig         = field(default_factory=BinanceConfig)
    polymarket: PolymarketConfig   = field(default_factory=PolymarketConfig)

    # ── Alerting ──────────────────────────────────────────────────────────
    telegram_bot_token: str  = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str    = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    discord_webhook_url: str = field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", ""))

    # ── Database ──────────────────────────────────────────────────────────
    db_url: str = "sqlite:///data/alphacopy.db"

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str  = "logs/alphacopy.log"


# Singleton config
CONFIG = GlobalConfig()
