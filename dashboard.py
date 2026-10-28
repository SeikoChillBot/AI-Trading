import csv
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

report = Path("reports/latest.csv")
history = Path("reports/history.csv")
if not report.exists():
    raise SystemExit("No portfolio report yet")
with report.open(newline="") as f:
    rows = list(csv.DictReader(f))
previous = []
if history.exists():
    with history.open(newline="") as f:
        previous = list(csv.DictReader(f))
seen = {(r["strategy"], r["candle_end_ms"]) for r in previous}
stamp = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y à %H:%M (heure de Paris)")
for r in rows:
    if (r["strategy"], r["candle_end_ms"]) not in seen:
        previous.append({"recorded_at": stamp, **r})
with history.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["recorded_at", *rows[0].keys()])
    writer.writeheader()
    writer.writerows(previous)

def spark(vals):
    if len(vals) < 2:
        return "·"
    vals = vals[-48:]
    lo, hi = min(vals), max(vals)
    return "".join("▁▂▃▄▅▆▇█"[min(7, int((v-lo)/(hi-lo)*7))] if hi > lo else "▄" for v in vals)

lines = [
    "# Tableau de bord — AI Trading",
    "",
    f"Actualisé : **{stamp}** · **{len(rows)} robots** · **20 USD fictifs chacun**",
    "",
    "> Simulation uniquement, aucun argent réel. Les frais de marché sont simplifiés et les résultats ne sont pas des prévisions.",
    "",
    "| Robot | Capital | Gain / perte | Évolution | Opérations |",
    "|---|---:|---:|---|---:|",
]
for r in sorted(rows, key=lambda x: float(x["return_pct"]), reverse=True):
    values = [float(x["capital_usd"]) for x in previous if x["strategy"] == r["strategy"]]
    lines.append(f'| {r["strategy"]} | {float(r["capital_usd"]):.2f} $ | {float(r["return_pct"]):+.2f} % | {spark(values)} | {r["trades"]} |')
lines += [
    "",
    "## Comprendre les résultats",
    "",
    "- **Capital** : valeur actuelle du portefeuille fictif, crypto comprise.",
    "- **Gain / perte** : variation depuis les 20 $ initiaux.",
    "- **Évolution** : mini-courbe des 48 derniers relevés (échelle propre à chaque robot).",
    "- **Opérations** : nombre d'achats et de ventes fictifs.",
    "",
    "[Historique détaillé](reports/history.csv) · [Positions actuelles](state/portfolios.json)",
    "",
    "**Limites :** simulation en USD, frais forfaitaires de 0,1 %, sans spread ni glissement. Les transactions sont exécutées au prix de clôture du signal : biais favorable à corriger.",
]
Path("DASHBOARD.md").write_text("\n".join(lines) + "\n")
