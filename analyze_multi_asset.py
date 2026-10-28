"""Descriptive, forward-only statistics for independently recorded non-crypto paper robots."""
import csv
import json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

LATEST=Path("reports/multi_asset_latest.csv")
HISTORY=Path("reports/multi_asset_history.csv")
ORDERS=Path("reports/multi_asset_orders.csv")
STATE=Path("state/multi_asset_portfolios.json")
OUT=Path("reports/multi_asset_metrics.json")


def read(path):
    if not path.exists():return []
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))


def drawdown(values):
    high=0;worst=0
    for value in values:
        v=float(value)
        if v<=0:continue
        high=max(high,v)
        if high:worst=max(worst,100*(high-v)/high)
    return round(worst,4)


def complete_trades(events):
    cost=None;profits=[]
    for e in events:
        if e.get("status")!="SIMULATED_FILL":continue
        if e.get("side")=="BUY":
            if cost is None:cost=-float(e["net_usd"])
        elif e.get("side")=="SELL" and cost is not None:
            profits.append(float(e["net_usd"])-cost)
            cost=None
    return profits


def build_report(rows,history,orders,state):
    expected=state.get("initial_per_strategy_usd")
    if expected!=1000 or state.get("schema")!=1 or len(rows)!=18:
        raise ValueError("Multi-market consistency error")
    hist=defaultdict(list)
    for x in history:hist[x["strategy"]].append(x)
    trades=defaultdict(list)
    for x in orders:trades[x["strategy"]].append(x)
    started=datetime.fromisoformat(state["created"])
    updated=datetime.fromisoformat(state["updated"])
    elapsed_days=max(0,(updated-started).total_seconds()/86400)
    grouped=defaultdict(list)
    metrics=[]
    for row in rows:
        key=row["strategy"]
        capital=float(row["capital_usd"])
        series=[expected]+[float(x["capital_usd"]) for x in hist[key]]
        completed=complete_trades(trades[key])
        win=[p for p in completed if p>0]
        loss=[p for p in completed if p<0]
        quote_quality=row.get("pricing_quality","UNKNOWN")
        eligible=elapsed_days>=30 and len(completed)>=20 and quote_quality not in ("STALE","NO_DATA")
        result={"strategy":key,"asset":row["asset"],"market":row["market"],
            "capital_usd":round(capital,5),"initial_usd":expected,
            "return_pct":round(100*(capital/expected-1),4),
            "max_observed_drawdown_pct":drawdown(series),"observations":len(hist[key]),
            "closed_roundtrips":len(completed),"profitable":len(win),
            "win_rate_pct":round(100*len(win)/len(completed),2) if completed else None,
            "profit_factor":round(sum(win)/abs(sum(loss)),4) if loss else None,
            "fees_usd":float(row["fees_usd"]), "open_position":row["position"]=="INVESTED",
            "pricing_quality":quote_quality,"evaluable":eligible,
            "caution":"Securities dividends/splits not modeled; FX ECB rate is non-executable"}
        metrics.append(result);grouped[row["market"]].append(result)
    groups=[]
    for market,values in grouped.items():
        starting=sum(v["initial_usd"] for v in values)
        latest=sum(v["capital_usd"] for v in values)
        groups.append({"market":market,"strategies":len(values),
            "initial_usd":starting,"capital_usd":round(latest,5),
            "return_pct":round(100*(latest/starting-1),4),
            "evaluable_count":sum(v["evaluable"] for v in values)})
    starting=sum(float(r["initial_usd"]) for r in rows)
    final=sum(float(r["capital_usd"]) for r in rows)
    return {"version":1,"model":"multi_asset_paper_v1",
        "started_at":state["created"],"updated_at":state["updated"],
        "elapsed_days":round(elapsed_days,4),"starting_usd":starting,
        "capital_usd":round(final,5),"return_pct":round(100*(final/starting-1),4),
        "evaluated_count":sum(v["evaluable"] for v in metrics),
        "qualified_after_days":30,"qualified_after_closed_trades":20,
        "groups":groups,"strategies":metrics,
        "warning":"Exploratory paper research. Yahoo quote source unofficial and delayed. FX reference not executable. Dividends, corporate actions, fees/taxes may differ. No statistical inference without out-of-sample testing."}


def main():
    if not STATE.exists() or not LATEST.exists() or not HISTORY.exists():
        print("Multi-asset evaluation skipped until first verified report")
        return
    state=json.loads(STATE.read_text(encoding="utf-8"))
    report=build_report(read(LATEST),read(HISTORY),read(ORDERS),state)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Multi-asset: statistics for",len(report["strategies"]),
          "strategies; qualified",report["evaluated_count"])


if __name__=="__main__":
    main()
