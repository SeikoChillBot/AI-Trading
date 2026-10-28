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
