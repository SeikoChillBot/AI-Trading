"""Kraken 1-hour, source-checked, forward-only intraday paper research.

Historical choices use an earlier training window; unseen periods are scored
after fees. A separate paper candidate is registered at zero PnL and only
observed future closed candles may affect its imaginary $20 equity.
No broker, prediction guarantee, real execution or LLM-generated Python.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"reports/intraday_research.json"
STATE=ROOT/"state/intraday_paper.json"
PAIRS={"BTCUSD":"XBTUSD","ETHUSD":"ETHUSD","SOLUSD":"SOLUSD"}
GRID=[(kind,period,band) for kind in ("trend","reversion")
      for period in (8,16,24) for band in (.004,.008)]
COST=.009
CAPITAL=20.0

def read(path):
    try:
        x=json.loads(Path(path).read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {}
    except (OSError,ValueError):
        return {}

def fetch(symbol, now, get=requests.get):
    r=get("https://api.kraken.com/0/public/OHLC",
          params={"pair":PAIRS[symbol],"interval":60},
          headers={"User-Agent":"SeikoTradingResearch/1.0"},timeout=18)
    r.raise_for_status()
    payload=r.json()
    if payload.get("error"):
        raise ValueError("Kraken source error")
    result=payload.get("result",{})
    pages=[v for k,v in result.items() if k!="last" and isinstance(v,list)]
    if len(pages)!=1:raise ValueError("Missing or ambiguous Kraken pair")
    rows=[]
    for bar in pages[0]:
        t=int(bar[0])
        if t+3600>now.timestamp()-120:
            continue
        opening=float(bar[1]);closing=float(bar[4])
        if not all(math.isfinite(x) and x>0 for x in (opening,closing)):
            raise ValueError("Invalid OHLC price")
        rows.append({"t":t,"open":opening,"close":closing})
    if len(rows)<480:raise ValueError("Insufficient closed hourly observations")
    if any(rows[i]["t"]-rows[i-1]["t"]!=3600 for i in range(1,len(rows))):
        raise ValueError("Missing hour; do not invent price history")
    if not 0<now.timestamp()-(rows[-1]["t"]+3600)<3*3600:
        raise ValueError("Stale hourly source")
    return rows

def action(bars,index,parameter,held):
    kind,period,band=parameter
    if index<period+1:return "WAIT"
    closes=[bar["close"] for bar in bars[index-period:index]]
    mean=sum(closes)/period
    last=closes[-1]
    if kind=="trend":
        return ("SELL" if last<mean*(1-band) else "WAIT") if held else (
            "BUY" if last>mean*(1+band) else "WAIT")
    return ("SELL" if last>=mean else "WAIT") if held else (
        "BUY" if last<mean*(1-band) else "WAIT")

def simulate(bars,parameter,start,end,cost=COST):
    cash,units=CAPITAL,0.0
    dd,peak=0.0,CAPITAL
    sells,orders=0,0
    for i in range(start,end):
        order=action(bars,i,parameter,units>0)
        price=bars[i]["open"]
        if order=="BUY" and units==0:
            units=cash/(price*(1+cost));cash=0.0;orders+=1
        elif order=="SELL" and units>0:
            cash=units*price*(1-cost);units=0.0;orders+=1;sells+=1
        equity=cash+units*bars[i]["close"]*(1-cost)
        if not math.isfinite(equity) or equity<0:raise ValueError("Non-finite equity")
        peak=max(peak,equity)
        dd=max(dd,(peak-equity)/peak*100)
    equity=cash+units*bars[end-1]["close"]*(1-cost)
    return {"return_pct":round(100*(equity/CAPITAL-1),5),
            "max_drawdown_pct":round(dd,5),"closed_trades":sells,
            "orders":orders}

def choose(bars,lo,hi):
    ranked=[]
    for parameter in GRID:
        p=simulate(bars,parameter,lo,hi)
        score=p["return_pct"]-.7*p["max_drawdown_pct"]-.03*p["orders"]
        ranked.append((score,GRID.index(parameter),parameter))
    return max(ranked,key=lambda x:(x[0],-x[1]))[2]

def evidence(bars):
    if len(bars)<480:raise ValueError("Insufficient independent test windows")
    folds=[]
    # Only select using previous 240 hours; test on the next 120 hours.
    for start in (len(bars)-240,len(bars)-120):
        p=choose(bars,start-240,start)
        run=simulate(bars,p,start,start+120)
        stress=simulate(bars,p,start,start+120,COST*2)
        hold=100*((CAPITAL/(bars[start]["open"]*(1+COST))*
                  bars[start+119]["close"]*(1-COST))/CAPITAL-1)
        folds.append({"test_started":bars[start]["t"],"test_ended":bars[start+119]["t"],
                      "parameter":{"kind":p[0],"period":p[1],"threshold":p[2]},
                      "net_return_pct":run["return_pct"],
                      "excess_vs_hold_points":round(run["return_pct"]-hold,5),
                      "double_cost_return_pct":stress["return_pct"],
                      "max_drawdown_pct":run["max_drawdown_pct"],
                      "closed_trades":run["closed_trades"]})
    return {"folds":folds,
            "avg_net_return_pct":round(sum(f["net_return_pct"] for f in folds)/len(folds),5),
            "avg_excess_vs_hold":round(sum(f["excess_vs_hold_points"] for f in folds)/len(folds),5),
            "max_drawdown_pct":max(f["max_drawdown_pct"] for f in folds),
            "proven_profitable":False}

def create_candidate(bars,now):
    p=choose(bars,len(bars)-240,len(bars))
    return {"created_at":now.isoformat(),"parameter":list(p),
            "last_t":bars[-1]["t"],"cash":CAPITAL,"units":0.0,
            "peak":CAPITAL,"max_dd_pct":0.0,"observations":0,
            "closed_trades":0,"state":"waiting_for_future_hour",
            "capital_usd":CAPITAL,"version":1}

def advance(bars,record,now):
    previous=next((i for i,b in enumerate(bars) if b["t"]==record["last_t"]),None)
    if previous is None:raise ValueError("Missing candidate registration candle")
    fresh=bars[previous+1:]
    if len(fresh)>3:raise ValueError("Missed live observation gap")
    for bar in fresh:
        i=next(i for i,b in enumerate(bars) if b["t"]==bar["t"])
        signal=action(bars,i,tuple(record["parameter"]),record["units"]>0)
        price=bar["close"] # Delayed observed-close paper proxy, not a real fill.
        if signal=="BUY" and record["units"]==0:
            record["units"]=record["cash"]/(price*(1+COST))
            record["cash"]=0.0
        elif signal=="SELL" and record["units"]>0:
            record["cash"]=record["units"]*price*(1-COST)
            record["units"]=0.0
            record["closed_trades"]+=1
        equity=record["cash"]+record["units"]*price*(1-COST)
        record["peak"]=max(record["peak"],equity)
        record["max_dd_pct"]=max(record["max_dd_pct"],
                                 (record["peak"]-equity)/record["peak"]*100)
        record["capital_usd"]=round(equity,5)
        record["observations"]+=1
        record["last_t"]=bar["t"]
        record["state"]="forward_hourly_observations"
    return record

def build(now, get=requests.get, old=None):
    old=old if isinstance(old,dict) else {}
    previous=old.get("assets",{})
    previous=previous if isinstance(previous,dict) else {}
    state={}
    report={"schema":1,"generated_at":now.isoformat(),"type":"kraken_1h_intraday_research",
            "source":"Kraken public 60m OHLC, only closed candles",
            "status":"available","assets":{},"errors":{},
            "real_orders":False,"automatic_promotion":False,
            "execution_limitation":"Delayed close paper proxy, not an executable order book fill.",
            "funds_real_usd":0}
    for symbol in PAIRS:
        try:
            bars=fetch(symbol,now,get)
            test=evidence(bars)
            candidate=previous.get(symbol)
            if not isinstance(candidate,dict):
                candidate=create_candidate(bars,now)
            else:
                try:candidate=advance(bars,candidate,now)
                except ValueError as error:
                    candidate=create_candidate(bars,now)
                    candidate["version"]=int(previous[symbol].get("version",1))+1
                    candidate["reset_reason"]=str(error)[:140]
            state[symbol]=candidate
            report["assets"][symbol]={
                "last_closed_hour_utc":datetime.fromtimestamp(bars[-1]["t"],timezone.utc).isoformat(),
                "historical_study":test,
                "paper_forward":{"version":candidate["version"],
                    "status":candidate["state"],"observations":candidate["observations"],
                    "capital_usd":candidate["capital_usd"],
                    "net_return_pct":round(100*(candidate["capital_usd"]/CAPITAL-1),5),
                    "max_drawdown_pct":round(candidate["max_dd_pct"],4),
                    "closed_trades":candidate["closed_trades"],
                    "created_at":candidate["created_at"]},
                "paper_only":True,
            }
        except (requests.RequestException,ValueError,TypeError,KeyError,OverflowError) as error:
            report["errors"][symbol]=type(error).__name__+": "+str(error)[:140]
    if len(report["errors"])==len(PAIRS):report["status"]="unavailable"
    elif report["errors"]:report["status"]="partial"
    return report,{"schema":1,"assets":state | {k:v for k,v in previous.items() if k not in state}}

def main():
    now=datetime.now(timezone.utc)
    report,state=build(now,old=read(STATE))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Hourly studies",len(report["assets"]),"errors",len(report["errors"]))

if __name__=="__main__":main()
