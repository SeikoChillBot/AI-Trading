"""Prospective, independent paper shadow accounts for LLM-suggested bot settings.

No historical backfill or real exchange execution. Signals are produced after
a closed candle and executed at the next OBSERVED closed reference quote, with
a conservative fee/spread proxy. This is not a live order-book fill.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from research.robot_tuning import TUNABLE_CRYPTO, TUNABLE_MULTI

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "state/robot_evolution_state.json"
STATE = ROOT / "state/robot_shadow_state.json"
OUTPUT = ROOT / "reports/robot_shadow_observations.json"
INITIAL = 20.0

def read(path):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}

def account():
    return {"cash":INITIAL, "units":0.0, "pending":"WAIT", "closed_trades":0,
            "fees":0.0, "peak":INITIAL, "max_drawdown_pct":0.0,
            "net_return_pct":0.0}

def start(candidate, candle_id):
    return {"created_at":candidate["created_at"],"entry_scale":candidate["entry_scale"],
            "last_candle":candle_id, "observations":0, "missed":0,
            "control":account(), "candidate":account(), "stress":account()}

def process_one(record, candle_id, close, signal_fn, cost):
    if candle_id <= record["last_candle"]:
        return record
    if not 0 < close < 1e9 or not math.isfinite(close):
        raise ValueError("Invalid observed market reference")
    # All accounts receive exactly the same price observation.
    for key, scale, expense in (
        ("control",1.0,cost),("candidate",record["entry_scale"],cost),
        ("stress",record["entry_scale"],min(cost*2,.1))):
        p = record[key]
        pending = p.get("pending", "WAIT")
        if pending == "BUY" and not p["units"] and p["cash"] > 0:
            budget = p["cash"]
            p["fees"] += budget*expense/(1+expense)
            p["units"] = budget/(close*(1+expense))
            p["cash"] = 0.0
        elif pending == "SELL" and p["units"] > 0:
            gross = p["units"]*close
            p["fees"] += gross*expense
            p["cash"] = gross*(1-expense)
            p["units"] = 0.0
            p["closed_trades"] += 1
        p["pending"] = signal_fn(scale, p["units"] > 0)
        equity = p["cash"]+p["units"]*close*(1-expense)
        if not math.isfinite(equity) or equity < 0:
            raise ValueError("Non-finite simulated shadow equity")
        p["peak"] = max(p["peak"],equity)
        p["max_drawdown_pct"] = max(p["max_drawdown_pct"],
                                    100*(p["peak"]-equity)/p["peak"])
        p["net_return_pct"] = 100*(equity/INITIAL-1)
    record["last_candle"] = candle_id
    record["observations"] += 1
    return record

def summarize(now, candidate, record):
    if not record:
        return None
    return {"source":"independent_forward_shadow_v1",
            "created_at":candidate["created_at"],"observed_at":now.isoformat(),
            "entry_scale":record["entry_scale"],
            "observations":record["observations"],"missed_observations":record["missed"],
            "control":{k:round(record["control"][k],5) for k in
                       ("net_return_pct","closed_trades","max_drawdown_pct","fees")},
            "candidate":{**{k:round(record["candidate"][k],5) for k in
                          ("net_return_pct","closed_trades","max_drawdown_pct","fees")},
                        "stress_net_return_pct":round(record["stress"]["net_return_pct"],5)},
            "ready_for_real_orders":False,
            "model":"delayed_observed_close_with_modeled_fees_not_orderbook",
            "not_independent_of_market_regime":True}

def observe_crypto(market, now=None):
    from bot import STRATEGIES, TIMEFRAMES, decide
    now = now or datetime.now(timezone.utc)
    proposals = read(CANDIDATES).get("candidates", {})
    state = read(STATE)
    records = state.get("accounts", {}) if isinstance(state.get("accounts", {}), dict) else {}
    for name,symbol,mode in STRATEGIES:
        candidate = proposals.get(name, {})
        if name not in TUNABLE_CRYPTO or candidate.get("status") not in ("shadow_pending", "automatically_promoted_paper_only"):
            continue
        points = market.get((symbol, TIMEFRAMES[name]), [])
        if len(points) < 60:
            continue
        candle_id,price = points[-1]
        old = records.get(name, {})
        if (old.get("created_at") != candidate.get("created_at")
                or old.get("entry_scale") != candidate.get("entry_scale")):
            records[name] = start(candidate,candle_id)
            continue
        if candle_id <= old["last_candle"]:
            continue
        # Never replay many missed candles and claim continuous live observation.
        if candle_id-old["last_candle"] > TIMEFRAMES[name]*60000*3:
            old["missed"] += 1
            old["last_candle"] = candle_id
            for key in ("control","candidate","stress"):
                old[key]["pending"] = "WAIT"
            continue
        closes=[v for _,v in points]
        def action(scale,holding):
            return decide(mode,closes,holding,old["candidate"] if scale!=1 else
                          old["control"],scale).upper()
        records[name] = process_one(old,candle_id,price,action,.009)
    _write(now,records)

def observe_multi(sources, now=None):
    from multi_asset_sim import evaluate
    now = now or datetime.now(timezone.utc)
    proposals=read(CANDIDATES).get("candidates", {})
    state=read(STATE)
    records=state.get("accounts", {}) if isinstance(state.get("accounts",{}),dict) else {}
    for name,candidate in proposals.items():
        if name not in TUNABLE_MULTI or candidate.get("status") not in ("shadow_pending","automatically_promoted_paper_only"):
            continue
        symbol=name.rsplit("_",1)[0].upper()
        quote=sources.get(symbol,{})
        if not quote.get("eligible") or not quote.get("previous") or not quote.get("price"):
            continue
        day=quote["previous"][-1]["date"]
        candle_id=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())*1000
        price=float(quote["price"])
        old=records.get(name,{})
        if (old.get("created_at")!=candidate.get("created_at")
                or old.get("entry_scale")!=candidate.get("entry_scale")):
            records[name]=start(candidate,candle_id)
            continue
        if candle_id <= old["last_candle"]:
            continue
        if candle_id-old["last_candle"]>5*86400000:
            old["missed"]+=1;old["last_candle"]=candle_id
            for key in ("control","candidate","stress"):
                old[key]["pending"]="WAIT"
            continue
        previous=quote["previous"]
        def action(scale,held):
            return evaluate("trend20",previous,held,scale)[0]
        records[name]=process_one(old,candle_id,price,action,.003 if symbol!="EURUSD" else .006)
    _write(now,records)

def _write(now,records):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({"schema":1,"accounts":records},ensure_ascii=False,indent=2)+"\n",
                     encoding="utf-8")
    candidates=read(CANDIDATES).get("candidates",{})
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "schema":1,"observed_at":now.isoformat(),
        "assets":{name:summarize(now,candidates[name],record)
                  for name,record in records.items()
                  if name in candidates and record.get("created_at")==candidates[name].get("created_at")},
        "real_orders":False,"warning":"Fee-modeled, delayed-close forward paper comparisons; no execution guarantees.",
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
