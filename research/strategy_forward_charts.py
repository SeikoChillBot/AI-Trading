"""Append-only daily equity observations for prospective strategy charts."""
from __future__ import annotations
import json
import math
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/"state/strategy_forward_positions.json"
REPORT=ROOT/"reports/strategy_forward.json"
HISTORY=ROOT/"state/strategy_forward_equity_history.json"
OUTPUT=ROOT/"reports/strategy_forward_equity_charts.json"

def load(path):
    try:
        obj=json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else {}
    except (OSError,ValueError):
        return {}

def build(forward,positions,previous):
    if (forward.get("schema")!=1 or forward.get("real_orders") is not False
        or forward.get("robots_modified") is not False or positions.get("schema")!=1):
        raise ValueError("invalid_forward_sources")
    tracks=positions.get("tracks",{})
    if not isinstance(tracks,dict):
        raise ValueError("invalid_tracks")
    old=previous.get("series",{}) if isinstance(previous,dict) else {}
    old=old if isinstance(old,dict) else {}
    series={}
    for item in forward.get("trials",[]):
        if not isinstance(item,dict):
            continue
        key=item.get("id")
        track=tracks.get(key)
        if not isinstance(key,str) or not isinstance(track,dict) or track.get("id")!=key:
            continue
        rows=old.get(key,[])
        rows=[x for x in rows if isinstance(x,dict) and type(x.get("t")) is int
              and isinstance(x.get("equity_usd"),(int,float))
              and math.isfinite(x["equity_usd"]) and x["equity_usd"]>=0][-365:] if isinstance(rows,list) else []
        t=track.get("last_t")
        equity=track.get("value_usd")
        benchmark=track.get("hold_net_pct")
        if (type(t) is int and type(equity) in (int,float)
            and math.isfinite(equity) and equity>=0
            and type(benchmark) in (int,float) and math.isfinite(benchmark)
            and type(track.get("observed_days")) is int and track["observed_days"]>0):
            # Never fabricate past equity points from the final performance.
            if not rows or t>rows[-1]["t"]:
                rows.append({"t":t,"equity_usd":round(equity,6),
                             "hold_equity_usd":round(20*(1+benchmark/100),6)})
        series[key]=rows[-365:]
    report={"schema":1,"generated_at":forward.get("generated_at"),
            "tracked":len(series),"series":series,
            "no_backfilled_points":True,"real_orders":False,
            "warning":"Observed forward-only paper marks, not executable market fills."}
    return report,{"schema":1,"series":series}

def main():
    report,state=build(load(REPORT),load(STATE),load(HISTORY))
    for path,obj in ((OUTPUT,report),(HISTORY,state)):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Forward equity chart tracks:",report["tracked"])

if __name__=="__main__":
    main()
