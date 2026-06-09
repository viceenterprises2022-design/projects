from data_collectors.base import BaseCollector
from data_collectors.general import GeneralCollector
from data_collectors.academia import AcademiaCollector
from data_collectors.news import NewsCollector
from data_collectors.india_stocks import IndiaStocksCollector
from data_collectors.us_stocks import UsStocksCollector
from data_collectors.crypto import CryptoCollector

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
