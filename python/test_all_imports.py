# python/test_all_imports.py
"""Verifica che tutti i moduli si importino senza errori."""

import sys
from pathlib import Path

# Assicura che python/ sia nel path
sys.path.insert(0, str(Path(__file__).parent))

tests = [
    ("config",                   "from config import DATABASE, SUPPORTED_SPORTS"),
    ("db_connector",             "from db_connector import DB"),
    ("collectors/__init__",      "from collectors import OddsCollector, ResultsCollector"),
    ("collectors/odds_collector","from collectors.odds_collector import OddsCollector"),
    ("collectors/results_coll.", "from collectors.results_collector import ResultsCollector"),
    ("models/__init__",          "from models import PoissonModel, EloModel, KellyCriterion, ValueFinder"),
    ("models/poisson_model",     "from models.poisson_model import PoissonModel"),
    ("models/elo_model",         "from models.elo_model import EloModel"),
    ("models/kelly",             "from models.kelly import KellyCriterion"),
    ("models/value_finder",      "from models.value_finder import ValueFinder"),
    ("ai/__init__",              "from ai import ReportGenerator"),
    ("ai/report_generator",      "from ai.report_generator import ReportGenerator"),
]

print("\n" + "=" * 55)
print("  🔬 OddsLab — Test Import Moduli")
print("=" * 55)

errors = 0
for name, import_str in tests:
    try:
        exec(import_str)
        print(f"  ✅  {name:<30} OK")
    except Exception as e:
        print(f"  ❌  {name:<30} ERRORE: {e}")
        errors += 1

print("=" * 55)
if errors == 0:
    print("  🎉 TUTTI I MODULI IMPORTATI CORRETTAMENTE!")
    print("  Puoi eseguire: python main.py")
else:
    print(f"  ⚠️  {errors} errori trovati. Controlla sopra.")
print("=" * 55 + "\n")