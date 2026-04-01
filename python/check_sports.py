# python/check_sports.py
"""Mostra tutti gli sport disponibili e il loro stato."""

from collectors.odds_collector import OddsCollector
from db_connector import DB

collector = OddsCollector()
sports = collector.get_available_sports()

print("\n" + "=" * 70)
print("  🔍 Sport Disponibili su The Odds API")
print("=" * 70)

# Raggruppa per categoria
categories = {}
for s in sports:
    group = s.get('group', 'Altro')
    if group not in categories:
        categories[group] = []
    categories[group].append(s)

for group, items in sorted(categories.items()):
    print(f"\n📂 {group}")
    print(f"   {'Chiave API':<45} {'Nome':<30} {'Attivo'}")
    print(f"   {'-' * 80}")
    for s in items:
        active = "✅" if s.get('active') else "❌"
        print(f"   {s['key']:<45} {s['title']:<30} {active}")

# Conta
active_count = sum(1 for s in sports if s.get('active'))
print(f"\n{'=' * 70}")
print(f"  Totale: {len(sports)} sport | {active_count} attivi ora")
print(f"{'=' * 70}")

DB.close()