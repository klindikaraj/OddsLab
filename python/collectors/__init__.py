# python/collectors/__init__.py
"""Modulo per la raccolta dati da API esterne."""

from .odds_collector import OddsCollector
from .results_collector import ResultsCollector

__all__ = ['OddsCollector', 'ResultsCollector']