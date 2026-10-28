import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from fx_reference import load_fx


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# Keep the 2026-10-28 legacy experiment untouched and visibly separate.
# Display the forward-only, conservative model only after its first complete run.
real_state_path = Path('state/realistic_portfolios.json')
real_report = Path('reports/realistic_latest.csv')
real_history = Path('reports/realistic_history.csv')
real_orders = Path('reports/realistic_orders.csv')
realistic = real_state_path.exists() and real_report.exists() and real_history.exists()
if realistic:
    state = json.loads(real_state_path.read_text(encoding='utf-8'))
    rows = read_csv(real_report)
    history = read_csv(real_history)
    if state.get('version') != 2 or len(rows) != 18 or any(r.get('strategy') is None for r in rows):
        raise RuntimeError('Incomplete realistic simulation: refusing to mix histories')
    data = {
        'model': 'realistic_v2',
        'updated': state['updated'],
        'launched_at': state['created'],
        'rows': rows,
        'history': history,
        'orders': read_csv(real_orders)[-100:],
        'assumptions': state.get('market_assumptions', {}),
    }
else:
    state_path = Path('state/portfolios.json')
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    data = {
        'model': 'legacy_v1',
        'updated': state.get('updated', datetime.now(timezone.utc).isoformat()),
        'launched_at': '2026-10-28T06:36:00Z',
        'rows': read_csv('reports/latest.csv'),
        'history': read_csv('reports/history.csv'),
        'orders': [],
        'assumptions': {},
    }
# FX is a display-only quotation; it never enters the trading calculations.
data['fx'] = load_fx()
catalog_path = Path('research/market_catalog.json')
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
required = {'id', 'title', 'family', 'status', 'risk', 'strategies', 'data',
            'execution', 'constraint', 'source', 'examples', 'description'}
allowed_status = {'active', 'connect', 'research', 'high_risk'}
markets = catalog.get('markets', [])
ids = [market.get('id') for market in markets]
if (catalog.get('schema_version') != 1 or len(markets) < 8
        or len(set(ids)) != len(ids) or any(not required.issubset(market) for market in markets)
        or any(market['status'] not in allowed_status for market in markets)
        or any(not market['strategies'] for market in markets)
        or any(not market['source'].startswith('https://') for market in markets)
        or {m['id'] for m in markets if m['status'] == 'active'} != {'crypto'}):
    raise RuntimeError('Unvalidated market catalog, refusing to publish unverified activity')
# Research ideas never participate in simulated balances or performance calculations.
data['market_catalog'] = catalog
# Multi-asset experiment is fully independent: separate capital, orders and history.
multi_state_path = Path("state/multi_asset_micro_portfolios.json")
multi_report_path = Path("reports/multi_asset_micro_latest.csv")
multi_history_path = Path("reports/multi_asset_micro_history.csv")
multi_orders_path = Path("reports/multi_asset_micro_orders.csv")
multi_sources_path = Path("reports/multi_asset_micro_sources.json")
multi = {"ready": False, "rows": [], "history": [], "orders": [],
         "sources": {}, "started_at": None, "updated_at": None,
         "initial_per_strategy_usd": 20}
if multi_state_path.exists() and multi_report_path.exists() and multi_history_path.exists():
    multi_state = json.loads(multi_state_path.read_text(encoding="utf-8"))
    multi_rows = read_csv(multi_report_path)
    keys = [r.get("strategy") for r in multi_rows]
    if (multi_state.get("schema") != 2 or len(multi_rows) != 18
            or len(set(keys)) != 18
            or multi_state.get("initial_per_strategy_usd") != 20):
        raise RuntimeError("Multi-asset state invalid: refuse to publish misleading totals")
    multi = {"ready": True, "rows": multi_rows,
             "history": read_csv(multi_history_path)[-720:],
             "orders": read_csv(multi_orders_path)[-100:],
             "sources": json.loads(multi_sources_path.read_text(encoding="utf-8"))
                 if multi_sources_path.exists() else {},
             "started_at": multi_state["created"], "updated_at": multi_state["updated"],
             "initial_per_strategy_usd": 20,
             "warnings": multi_state.get("feed_notes", {})}
data["multi_asset"] = multi
rows = data['rows']
history = data['history']
template = Path('site/index.html').read_text(encoding='utf-8')
optional = {
    '/*__CSS__*/': Path('site/theme.css').read_text(encoding='utf-8'),
    '/*__JS__*/': Path('site/app.js').read_text(encoding='utf-8'),
}
for marker, replacement in optional.items():
    if marker in template:
        template = template.replace(marker, replacement)
marker = '/*__DATA__*/{"updated":"En attente du premier relevé","rows":[],"history":[]}'
if template.count(marker) != 1:
    raise RuntimeError('Dashboard template marker missing or duplicated')
safe_json = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
template = template.replace(marker, safe_json)
Path('site/dashboard.html').write_text(template, encoding='utf-8')
print('Generated site/dashboard.html with', len(rows), 'portfolios and', len(history), 'history points')
