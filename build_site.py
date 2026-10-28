import csv
import json
from pathlib import Path
from datetime import datetime, timezone


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


rows = read_csv('reports/latest.csv')
history = read_csv('reports/history.csv')
state_path = Path('state/portfolios.json')
state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
data = {
    'updated': state.get('updated', datetime.now(timezone.utc).isoformat()),
    'launched_at': '2026-10-28T06:36:00Z',  # timestamp of first recorded simulation, not candle time
    'rows': rows,
    'history': history,
}
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
