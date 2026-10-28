"""Read-only, reproducible daily Kraken backtests with chronological holdouts.

Only complete daily candles; decision at previous close, estimated fill at
next day's open. No real orders, no modifications to the original 36 bots.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/"reports/challenger_walkforward.json"
SNAPSHOT = ROOT/"reports/challenger_candles.json"
PAIRS = {"BTCUSD":"XBTUSD", "ETHUSD":"ETHUSD", "SOLUSD":"SOLUSD"}
PARAMS = [{"window":w,"buffer":b} for w in (10,20,40) for b in (.005,.01,.02)]
CAPITAL = 20.
TRAIN = 240
TEST = 60
MIN_BARS = TRAIN + 2*TEST
# Conservative proxy: Kraken taker 0.8%, 0.05% slippage, 0.05%
# assumed half-spread, per side. No historic bid/ask is observed.
COST = .008 + .0005 + .0005

def number(v):
    x=float(v)
    if not math.isfinite(x) or x<=0:raise ValueError("Invalid price")
    return x

def validate(bars, now):
    if len(bars)<MIN_BARS:raise ValueError("Insufficient closed daily candles")
    for i,b in enumerate(bars):
        number(b["open"]);number(b["close"])
        if not 1e8 < b["t"] < now.timestamp():
            raise ValueError("Future or invalid candle timestamp")
        if i and b["t"]-bars[i-1]["t"]!=86400:
            raise ValueError("Missing/duplicated daily candle: no repair")
    if now.timestamp()-bars[-1]["t"]-86400>3*86400:
        raise ValueError("Outdated market data")

def fetch_kraken(symbol,now,get=requests.get):
    response=get("https://api.kraken.com/0/public/OHLC",
        params={"pair":PAIRS[symbol],"interval":1440},
        headers={"User-Agent":"SeikoResearch/1.0"},timeout=22)
    response.raise_for_status();data=response.json()
    if data.get("error"):raise ValueError(str(data["error"]))
    data=data.get("result",{})
    values=[v for k,v in data.items() if k!="last" and isinstance(v,list)]
    if len(values)!=1:raise ValueError("Kraken OHLC pair ambiguous")
    bars=[]
    for b in values[0]:
        stamp=int(b[0])
        # Exclude the current, still-running daily candle.
        if stamp+86400>now.timestamp()-600:continue
        bars.append({"t":stamp,"open":number(b[1]),"close":number(b[4])})
    validate(bars,now)
    return bars

def signal(bars,i,param,held):
    """At open(i), only closes through (i-1) may be read."""
    w,band=param["window"],param["buffer"]
    if i<w:return "WAIT"
    closes=[b["close"] for b in bars[i-w:i]]
    mean=sum(closes)/w;price=closes[-1]
    if not held and price>mean*(1+band):return "BUY"
    if held and price<mean*(1-band):return "SELL"
    return "WAIT"

def simulate(bars,param,start,end,cost=COST):
    """All in/out, $20 imaginary. Independent runs for each fold."""
    if start<max(PARAMS[-1]["window"],param["window"]) or end>len(bars) or start>=end:
        raise ValueError("Wrong segment boundaries")
    cash,units,fees=CAPITAL,0.,0.
    orders=exits=0
    peak=CAPITAL;max_dd=0.
    for i in range(start,end):
        action=signal(bars,i,param,units>0)
        opening=bars[i]["open"]
        if action=="BUY" and units==0:
            fees+=cash*cost/(1+cost)
            units=cash/(opening*(1+cost))
            cash=0.;orders+=1
        elif action=="SELL" and units>0:
            gross=units*opening
            fees+=gross*cost;cash=gross*(1-cost)
            units=0.;orders+=1;exits+=1
        # Mark the paper position as liquidatable after hypothetical exit fees.
        value=cash+units*bars[i]["close"]*(1-cost)
        if value<0 or not math.isfinite(value):raise ValueError("Invalid simulated equity")
        peak=max(value,peak)
        max_dd=max(max_dd,100*(peak-value)/peak)
    end_value=cash+units*bars[end-1]["close"]*(1-cost)
    return {"return_pct":round(100*(end_value/CAPITAL-1),5),
            "max_drawdown_pct":round(max_dd,5),
            "orders":orders,"completed_trades":exits,
            "paid_and_modeled_usd":round(fees,5)}

def hold(bars,start,end,cost=COST):
    if end<=start:raise ValueError("Invalid hold segment")
    amount=CAPITAL/(bars[start]["open"]*(1+cost))
    return round(100*(amount*bars[end-1]["close"]*(1-cost)/CAPITAL-1),5)
