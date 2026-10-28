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
    if start<0 or end>len(bars) or start>=end:
        raise ValueError("Wrong segment boundaries")
    cash,units,fees=CAPITAL,0.,0.
    orders=exits=0
    peak=CAPITAL;max_dd=0.
    for i in range(max(start,40),end):
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

def choose(bars,start,end):
    """Selection uses only this training segment, never later test data."""
    candidates=[]
    for param in PARAMS:
        performance=simulate(bars,param,start,end)
        score=(performance["return_pct"]-.55*performance["max_drawdown_pct"]
               -.05*performance["orders"])
        candidates.append((score,-param["window"],-param["buffer"],param))
    return max(candidates,key=lambda x:x[:3])[3]

def walkforward(bars):
    if len(bars)<MIN_BARS:raise ValueError("Not enough OOS data")
    folds=[]
    for test_start in range(TRAIN,len(bars)-TEST+1,TEST):
        train_start=test_start-TRAIN
        choice=choose(bars,train_start,test_start)
        outcome=simulate(bars,choice,test_start,test_start+TEST)
        stress=simulate(bars,choice,test_start,test_start+TEST,cost=COST*2)
        witness=hold(bars,test_start,test_start+TEST)
        folds.append({
            "train_first":bars[train_start]["t"],
            "train_last":bars[test_start-1]["t"],
            "test_first":bars[test_start]["t"],
            "test_last":bars[test_start+TEST-1]["t"],
            "parameters":choice,
            "oos_return_pct":outcome["return_pct"],
            "hold_return_pct":witness,
            "excess_vs_hold_points":round(outcome["return_pct"]-witness,5),
            "cost_x2_return_pct":stress["return_pct"],
            "observed_drawdown_pct":outcome["max_drawdown_pct"],
            "completed_trades":outcome["completed_trades"],
            "orders":outcome["orders"],
        })
    if len(folds)<2:raise ValueError("At least two blind windows required")
    mean=lambda field:round(sum(f[field] for f in folds)/len(folds),5)
    # The next paper candidate is selected on the most recent past prices.
    # Its parameters are frozen in the forward portfolio and not rewritten.
    latest=choose(bars,len(bars)-TRAIN,len(bars))
    return {
        "folds":folds,"fold_count":len(folds),
        "train_days":TRAIN,"test_days":TEST,
        "average_oos_return_pct":mean("oos_return_pct"),
        "average_oos_excess_vs_hold_points":mean("excess_vs_hold_points"),
        "average_oos_return_double_cost_pct":mean("cost_x2_return_pct"),
        "total_oos_closed_trades":sum(f["completed_trades"] for f in folds),
        "max_oos_drawdown_pct":max(f["observed_drawdown_pct"] for f in folds),
        "candidate_parameters":latest,
        "status":"research_only_not_proven",
    }

def build(now,source):
    instruments,issues,market={}, {}, {}
    for symbol in PAIRS:
        try:
            candles=source(symbol,now)
            validate(candles,now)
            digest=hashlib.sha256(json.dumps(candles,sort_keys=True,
                                              separators=(",",":")).encode()).hexdigest()
            result=walkforward(candles)
            instruments[symbol]={"source":"Kraken public daily OHLC (USD spot)",
                "source_sha256":digest,
                "first_closed_day":candles[0]["t"],
                "last_closed_day":candles[-1]["t"],
                "bars":len(candles),**result}
            market[symbol]=candles
        except (ValueError,TypeError,KeyError,IndexError,
                requests.RequestException) as exc:
            issues[symbol]=type(exc).__name__+": "+str(exc)[:200]
    report={
        "schema":1,"generated_at":now.isoformat(),
        "model":"kraken_daily_walkforward_v1",
        "instruments":instruments,"issues":issues,
        "candidate_count":len(instruments),
        "grid":PARAMS,"capital_per_candidate_usd":CAPITAL,
        "holdout_training":TRAIN,"holdout_test":TEST,
        "cost_per_side_assumed":COST,"real_orders":False,
        "live_strategy_changes":False,
        "warning":"Daily Kraken OHLC limited to ~720 bars. Next-open trades use modelled fees, not historic executable books. Repeated strategy search and multiple testing may overfit; out-of-sample results are not guaranteed returns."
    }
    return report,market

def main():
    now=datetime.now(timezone.utc)
    report,market=build(now,fetch_kraken)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    SNAPSHOT.write_text(json.dumps(market,separators=(",",":"))+"\n",encoding="utf-8")
    print("Historical challenger tests: %d instruments, %d source failures, 0 real orders" %
          (len(report["instruments"]),len(report["issues"])))

if __name__=="__main__":
    main()
