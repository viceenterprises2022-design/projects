import os, yaml, logging, colorlog
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def setup_logger(name):
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        log_colors={"DEBUG":"cyan","INFO":"green","WARNING":"yellow","ERROR":"red","CRITICAL":"bold_red"},
    ))
    logger = logging.getLogger(name)
    level = getattr(logging, os.getenv("LOG_LEVEL","INFO").upper())
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

class BotConfig:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            path = Path(__file__).parent.parent / "config.yaml"
            with open(path) as f:
                cls._instance._cfg = yaml.safe_load(f)
        return cls._instance

    def get(self, *keys, default=None):
        val = self._cfg
        for k in keys:
            if not isinstance(val, dict): return default
            val = val.get(k, default)
        return val

    @property
    def risk(self): return self._cfg.get("risk", {})
    @property
    def whale_filters(self): return self._cfg.get("whale_filters", {})
    @property
    def whale_wallets(self): return self._cfg.get("whale_wallets", [])
    @property
    def position_sizing(self): return self._cfg.get("position_sizing", {})
    @property
    def execution(self): return self._cfg.get("execution", {})
    @property
    def market_filters(self): return self._cfg.get("market_filters", {})
    @property
    def telegram(self): return self._cfg.get("telegram", {})
    @property
    def api(self): return self._cfg.get("api", {})
    @property
    def exit(self): return self._cfg.get("exit", {})
    @property
    def dry_run(self): return os.getenv("DRY_RUN","true").lower()=="true"
    @property
    def private_key(self):
        pk = os.getenv("PRIVATE_KEY","")
        if not pk: raise ValueError("PRIVATE_KEY not set in .env")
        return pk
    @property
    def funder_address(self): return os.getenv("FUNDER_ADDRESS","")
    @property
    def signature_type(self): return int(os.getenv("SIGNATURE_TYPE","1"))
    @property
    def telegram_token(self):
        t = os.getenv("TELEGRAM_BOT_TOKEN","")
        if not t: raise ValueError("TELEGRAM_BOT_TOKEN not set")
        return t
    @property
    def telegram_chat_id(self):
        c = os.getenv("TELEGRAM_CHAT_ID","")
        if not c: raise ValueError("TELEGRAM_CHAT_ID not set")
        return c

cfg = BotConfig()
