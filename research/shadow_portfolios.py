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
