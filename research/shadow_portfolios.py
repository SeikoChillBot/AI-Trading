"""Forward-only shadow challengers, independent from 36 running paper robots."""
from __future__ import annotations
import json
from pathlib import Path
import math
from datetime import datetime,timezone
from realistic_sim import pair_metadata,orderbook,executable_buy,executable_sell,estimated_liquidation
from research.walkforward import signal

ROOT=Path(__file__).resolve().parents[1]
BACKTEST=ROOT/"reports/challenger_walkforward.json"
MARKET=ROOT/"reports/challenger_candles.json"
STATE=ROOT/"state/shadow_challenger_portfolios.json"
REPORT=ROOT/"reports/shadow_challengers.json"
HISTORY=ROOT/"reports/shadow_challenger_history.jsonl"
ORDERS=ROOT/"reports/shadow_challenger_orders.jsonl"
START=20.

def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def append(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row,ensure_ascii=False)+"\n")

def valid_sources(report,market,now):
    accepted={}
    for asset,info in report.get("instruments",{}).items():
        bars=market.get(asset)
        if not isinstance(bars,list) or len(bars)<360:continue
        if bars[-1]["t"]!=info.get("last_closed_day"):continue
        if now.timestamp()-(bars[-1]["t"]+86400)>36*3600:continue
        param=info.get("candidate_parameters")
        if not isinstance(param,dict):continue
        if param.get("window") not in (10,20,40):continue
        if param.get("buffer") not in (.005,.01,.02):continue
        accepted[asset]=(info,bars,param)
    return accepted

def enroll(state,approved,now):
    state.setdefault("portfolios",{})
    for asset,(info,bars,param) in approved.items():
        if asset in state["portfolios"]:continue
        name="%s_ma%d_b%03d"%(asset.lower(),param["window"],round(param["buffer"]*10000))
        state["portfolios"][asset]={
            "id":name,"asset":asset,"parameters":dict(param),
            "created":now.isoformat(),"source_hash":info["source_sha256"],
            "last_closed_day":bars[-1]["t"],"cash":START,
            "units":0.,"fees":0.,"orders":0,"closed_trades":0,
            "last_equity":START,"price_quality":"not_yet_quoted"
        }
    return state

def step(row,bars,now,book,limits):
    """At most one new complete daily signal, using a freshly observed book."""
    if row["units"]<0 or row["cash"]<-1e-8:raise ValueError("Negative balance")
    last=bars[-1]["t"]
    if last<row["last_closed_day"]:raise ValueError("Market data regressed")
    events=[]
    fresh=0<=now.timestamp()-(last+86400)<=36*3600
    if last>row["last_closed_day"]:
        action=signal(bars,len(bars),row["parameters"],row["units"]>0) if fresh else "WAIT"
        if action in ("BUY","SELL"):
            trade,error=(executable_buy(row["cash"],book,limits) if action=="BUY"
                         else executable_sell(row["units"],book,limits))
            event={"at":now.isoformat(),"strategy":row["id"],"asset":row["asset"],
                   "signal_closed":last+86400,"action":action,
                   "status":"FILLED_PAPER" if trade else "REJECTED",
                   "reason":"Closed SMA" if trade else error}
            if trade:
                row["cash"] += trade["net"]
                row["units"]=row["units"]+trade["units"] if action=="BUY" else 0.0
                row["closed_trades"]+=int(action=="SELL")
                row["orders"]+=1
                row["fees"]+=trade["fee"]
                event.update(quantity=trade["units"],fee_usd=trade["fee"],
                             cash_delta=trade["net"])
            events.append(event)
        row["last_closed_day"]=last
    row['last_equity']=estimated_liquidation(row,book)
    return events

def main():
    now=datetime.now(timezone.utc)
    evaluation=load(BACKTEST) or {}
    candles=load(MARKET) or {}
    candidates=valid_sources(evaluation,candles,now)
    state=load(STATE) or {"schema":1,"created":now.isoformat(),"portfolios":{}}
    if state.get("schema")!=1:raise ValueError("Unexpected shadow state")
    enroll(state,candidates,now)
    events=[];errors={}
    if candidates:rules=pair_metadata()
    for asset,(info,bars,param) in candidates.items():
        symbol=asset+"T"
        try:
            book=orderbook(symbol)
            events.extend(step(state["portfolios"][asset],bars,now,book,rules[symbol]))
        except (ValueError,RuntimeError,KeyError) as exc:
            errors[asset]=type(exc).__name__+": "+str(exc)[:140]
    state["updated"]=now.isoformat()
    rows=[]
    for asset,item in state["portfolios"].items():
        rows.append({"id":item["id"],"asset":asset,"parameters":item["parameters"],
                     "capital_initial_usd":START,"capital_estimated_usd":item["last_equity"]})
    if state["portfolios"]:
        save(STATE,state)
    summary={"schema":1,"generated_at":now.isoformat(),
             "mode":"prospective_research_only",
             "created_at":state["created"],"robots":rows,
             "errors":errors,"new_order_events":len(events),
             "real_orders":False,"baseline_robots_modified":False,
             "warning":"First run enrolls without retrospective trades. Future signals use observed Kraken books and actual exchange minimums. $20 fictional capital, no investment advice."}
    save(REPORT,summary)
    append(ORDERS,events)
    append(HISTORY,[{"at":now.isoformat(),**row} for row in rows])
