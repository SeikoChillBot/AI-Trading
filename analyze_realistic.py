"""Evaluate forward-only paper-trading samples without claiming profitability.

Consumes append-only simulated snapshots and attempted orders.
All statistics are descriptive, not expected returns or trading signals.
"""
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LATEST = Path("reports/realistic_latest.csv")
HISTORY = Path("reports/realistic_history.csv")
ORDERS = Path("reports/realistic_orders.csv")
STATE = Path("state/realistic_portfolios.json")
OUT = Path("reports/realistic_metrics.json")
INITIAL_PER_ROBOT = 20.0
MIN_SAMPLE_DAYS = 14
MIN_COMPLETED_TRADES = 20


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def drawdown(equities):
    peak = float("-inf")
    worst = 0.0
    for equity in equities:
        value = float(equity)
        if value <= 0:
            continue
        peak = max(value,peak)
        if peak > 0:
            worst = max(worst, (peak-value)/peak)
    return round(worst*100,4)


def parse_time(value):
    return datetime.fromisoformat(str(value).replace("Z","+00:00"))


def roundtrips(orders):
    """A full entry/exit cycle, including both fees already in net_usd."""
    entry_cost = None
    pairs = []
    for order in orders:
        if order.get("status") != "FILLED_SIMULATED":
            continue
        side = order.get("side")
        if side == "BUY":
            entry_cost = -float(order["net_usd"])
        elif side == "SELL" and entry_cost is not None:
            proceeds = float(order["net_usd"])
            pairs.append({"profit_usd":proceeds-entry_cost,
                          "return_pct":100*(proceeds-entry_cost)/entry_cost if entry_cost else 0})
            entry_cost = None
    return pairs


def main():
    if not all(p.exists() for p in [LATEST,HISTORY,ORDERS,STATE]):
        raise SystemExit("Realistic data incomplete: no evaluation produced")
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("version") != 2:
        raise ValueError("Realistic schema version mismatch")
    now = parse_time(state["updated"])
    started = parse_time(state["created"])
    days = max(0,(now-started).total_seconds()/86400)
    rows = read_csv(LATEST)
    history = read_csv(HISTORY)
    orders = read_csv(ORDERS)
    if len(rows) != 18:
        raise ValueError("Incomplete 18 strategy universe")
    history_by = defaultdict(list)
    for row in history:
        history_by[row["strategy"]].append(row)
    orders_by = defaultdict(list)
    for event in orders:
        orders_by[event["strategy"]].append(event)
    hold_by_coin = {r["strategy"].split("_")[0]:float(r["return_pct"])
                    for r in rows if r["strategy"].endswith("_hold")}
    metrics=[]
    for row in rows:
        name=row["strategy"]
        coin=name.split("_")[0]
        value=float(row["capital_usd"])
        equity=[INITIAL_PER_ROBOT]+[float(h["capital_usd"]) for h in history_by[name]]
        events=orders_by[name]
        filled=[e for e in events if e.get("status")=="FILLED_SIMULATED"]
        rejected=[e for e in events if e.get("status")!="FILLED_SIMULATED"]
        completed=roundtrips(events)
        wins=[x["profit_usd"] for x in completed if x["profit_usd"]>0]
        losses=[x["profit_usd"] for x in completed if x["profit_usd"]<0]
        enough=(days>=MIN_SAMPLE_DAYS and len(completed)>=MIN_COMPLETED_TRADES)
        metrics.append({
            "strategy":name,"asset":row["asset"],"capital_usd":round(value,5),
            "profit_usd":round(value-INITIAL_PER_ROBOT,5),
            "return_pct":round((value/INITIAL_PER_ROBOT-1)*100,4),
            "max_observed_drawdown_pct":drawdown(equity),
            "fees_paid_usd":float(row["fees_usd"]),
            "rejected_orders":len(rejected),
            "filled_orders":len(filled),
            "completed_roundtrips":len(completed),
            "profitable_roundtrips":len(wins),
            "losing_roundtrips":len(losses),
            "win_rate_pct":round(100*len(wins)/len(completed),2) if completed else None,
            "realized_pnl_usd":round(sum(x["profit_usd"] for x in completed),5),
            "profit_factor":round(sum(wins)/abs(sum(losses)),4) if losses else None,
            "excess_vs_hold_pct_points":round(float(row["return_pct"])-hold_by_coin[coin],3)
                 if coin in hold_by_coin else None,
            "observation_count":len(equity)-1,
            "evaluable":enough,
            "quality":"sufficient_sample_for_review" if enough else "insufficient_sample",
        })
    chronological = defaultdict(dict)
    for h in history:
        chronological[h["recorded_at"]][h["strategy"]]=float(h["capital_usd"])
    capital = INITIAL_PER_ROBOT*len(rows)
    values=[capital]
    state_cap={r["strategy"]:INITIAL_PER_ROBOT for r in rows}
    for stamp,changes in sorted(chronological.items()):
        state_cap.update(changes)
        values.append(sum(state_cap.values()))
    report={
        "model":"realistic_v2",
        "calculated_at":datetime.now(timezone.utc).isoformat(),
        "started_at":state["created"],"updated_at":state["updated"],
        "elapsed_days":round(days,4),
        "initial_total_usd":capital,
        "latest_total_usd":round(sum(float(r["capital_usd"]) for r in rows),5),
        "total_return_pct":round(100*(sum(float(r["capital_usd"]) for r in rows)/capital-1),4),
        "total_max_observed_drawdown_pct":drawdown(values),
        "filled_orders":sum(m["filled_orders"] for m in metrics),
        "rejected_orders":sum(m["rejected_orders"] for m in metrics),
        "evaluated_strategies":sum(m["evaluable"] for m in metrics),
        "qualification_requirements":{"elapsed_days":MIN_SAMPLE_DAYS,
                                      "completed_roundtrips":MIN_COMPLETED_TRADES},
        "warning":"Statistiques descriptives seulement. Carnet instantane et slippage estime ne garantissent aucun prix d'execution reel.",
        "strategies":metrics,
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Realistic research metrics: ",len(metrics),"strategies; completed ",
          sum(m["completed_roundtrips"] for m in metrics),
          "cycles; qualified",report["evaluated_strategies"])


if __name__=="__main__":
    main()
