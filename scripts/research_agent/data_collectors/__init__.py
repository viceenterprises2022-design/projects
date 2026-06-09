from .base import BaseCollector
from .general import GeneralCollector
from .academia import AcademiaCollector
from .news import NewsCollector
from .india_stocks import IndiaStocksCollector
from .us_stocks import UsStocksCollector
from .crypto import CryptoCollector

COLLECTOR_MAP = {
    "general": GeneralCollector,
    "academia": AcademiaCollector,
    "world_news": NewsCollector,
    "india_stocks": IndiaStocksCollector,
    "us_stocks": UsStocksCollector,
    "crypto": CryptoCollector,
}

__all__ = [
    "BaseCollector",
    "GeneralCollector",
    "AcademiaCollector",
    "NewsCollector",
    "IndiaStocksCollector",
    "UsStocksCollector",
    "CryptoCollector",
    "COLLECTOR_MAP",
]
