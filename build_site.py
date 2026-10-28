import csv
import json
from pathlib import Path
from datetime import datetime, timezone

def read_csv(path):
    if not Path(path).exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

rows = read_csv("reports/latest.csv")
history = read_csv("reports/history.csv")
state_path = Path("state/portfolios.json")
state = json.loads(state_path.read_text()) if state_path.exists() else {}
data = {"updated": state.get("updated", datetime.now(timezone.utc).isoformat()), "rows": rows, "history": history}
template = Path("site/index.html").read_text()
marker = '/*__DATA__*/{"updated":"En attente du premier relevé","rows":[],"history":[]}'
if marker not in template:
    raise RuntimeError("Dashboard template marker missing")
safe_json = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
Path("site/dashboard.html").write_text(template.replace(marker, safe_json))
print("Generated site/dashboard.html with", len(rows), "portfolios and", len(history), "history points")
