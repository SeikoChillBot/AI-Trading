"""Independent, forward-only paper experiments requested by Gemini.

No order credentials, real orders, shorting, leverage or arbitrary model code.
A test starts only after fresh, matching observations; modeled close prices
are research proxies and cannot establish real-world execution.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IDEAS=ROOT/"reports/ai_research_proposals.json"
PULSE=ROOT/"reports/market_pulse.json"
CANDLES=ROOT/"reports/challenger_candles.json"
STATE=ROOT/"state/ai_placement_experiments.json"
REPORT=ROOT/"reports/ai_placement_experiments.json"
COST=.009
CAPITAL=20.0
ALLOWED={"BTCUSD","ETHUSD","SOLUSD"}
TRIGGERS={"market_uptrend","market_selloff","sampled_large_transfer"}


def read(path):
    try:
        x=json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {}
    except (OSError,ValueError):
        return {}


def eligible(now, idea, pulse):
    """Requires fresh, independently sourced market evidence; no forged whale buys."""
    if (not isinstance(idea,dict) or idea.get("asset") not in ALLOWED
            or idea.get("trigger") not in TRIGGERS
            or type(idea.get("horizon_days")) is not int
            or idea["horizon_days"] not in (1,3,7)):
        return False,"invalid_whitelisted_hypothesis"
    try:
        generated=datetime.fromisoformat(pulse["generated_at"])
        if generated.tzinfo is None or not 0 <= (now-generated).total_seconds() <= 12*3600:
            return False,"market_data_stale"
    except (KeyError,ValueError,TypeError):
        return False,"market_data_missing"
    asset=pulse.get("assets",{}).get(idea["asset"])
    if not isinstance(asset,dict):
        return False,"asset_observation_missing"
    trigger=idea["trigger"]
    if trigger=="sampled_large_transfer":
        transfers=pulse.get("large_transfers",{})
        if (transfers.get("state") not in ("observing","partial")
                or transfers.get("coverage") != "NOT_EXHAUSTIVE_first_page_only_per_contract"
                or int(transfers.get("new_in_sample",0)) < 1):
            return False,"no_fresh_public_large_transfer_sample"
    else:
        try:
            move=float(asset["change_7d_pct"])
            if not math.isfinite(move) or (trigger=="market_uptrend" and move<=0):
                return False,"uptrend_not_observed"
            if trigger=="market_selloff" and move>=0:
                return False,"selloff_not_observed"
        except (ValueError,KeyError,TypeError):
            return False,"invalid_market_direction"
    return True,"fresh_observation_present_not_predictive"


def evolve(now, ideas, pulse, candles, state):
    previous=state.get("trials",[])
    trials=[dict(x) for x in previous if isinstance(x,dict)][:12]
    outcomes=[]
    seen={x.get("id") for x in trials}
    new_requests=ideas.get("scenario_proposals",[]) if ideas.get("source")=="gemini_generate_content" else []
    if not isinstance(new_requests,list):
        new_requests=[]
    for item in new_requests[:2]:
        if not isinstance(item,dict):
            continue
        valid,why=eligible(now,item,pulse)
        if not valid:
            outcomes.append({"asset":item.get("asset"),"trigger":item.get("trigger"),
                             "status":"rejected_no_qualifying_observation","reason":why})
            continue
        bars=candles.get(item["asset"],[])
        if not isinstance(bars,list) or len(bars)<25:
            outcomes.append({"asset":item["asset"],"status":"rejected_market_history_unavailable"})
            continue
        seed=bars[-1]
        at=int(seed.get("t",0))
        if not 0 < now.timestamp()-at < 5*86400:
            outcomes.append({"asset":item["asset"],"status":"rejected_stale_daily_candle"})
            continue
        # Once per combination per calendar day; never re-open at past observations.
        identity="|".join([now.date().isoformat(),item["asset"],item["trigger"],str(item["horizon_days"])])
        key=hashlib.sha256(identity.encode()).hexdigest()[:15]
        if key in seen:
            continue
        if sum(x.get("status") in ("waiting_next_closed_day","in_paper_position")
               for x in trials)>=6:
            outcomes.append({"asset":item["asset"],"status":"rejected_experiment_capacity"})
            continue
        rec={
            "id":key,"asset":item["asset"],"trigger":item["trigger"],
            "horizon_days":item["horizon_days"],"created_at":now.isoformat(),
            "last_t":at,"status":"waiting_next_closed_day",
            "entry_price":None,"entry_day":None,"observations_after_entry":0,
            "units":0.0,"equity_usd":CAPITAL,"estimated_net_pct":0.0,
            "rationale":str(item.get("rationale",""))[:350],
            "observation_reason":why,"paper_only":True,
            "execution_type":"modeled_fills_at_later_observed_daily_close",
        }
        seen.add(key);trials.append(rec)
        outcomes.append({"asset":rec["asset"],"id":key,"status":"paper_experiment_registered"})
    for item in trials:
        if item.get("status") not in ("waiting_next_closed_day","in_paper_position"):
            continue
        bars=candles.get(item["asset"],[])
        previous_index=next((i for i,x in enumerate(bars) if x.get("t")==item["last_t"]),None)
        if previous_index is None:
            item["status"]="terminated_missing_prior_candle"
            continue
        next_bars=bars[previous_index+1:]
        if not next_bars:continue
        if len(next_bars)!=1 or next_bars[0].get("t") != item["last_t"]+86400:
            item["status"]="terminated_missing_observation"
            continue
        b=next_bars[0]
        price=float(b["close"])
        if not math.isfinite(price) or price<=0:
            item["status"]="terminated_invalid_price"
            continue
        if item["status"]=="waiting_next_closed_day":
            item["entry_price"]=price
            item["entry_day"]=int(b["t"])
            item["units"]=CAPITAL/(price*(1+COST))
            item["status"]="in_paper_position"
        else:
            item["observations_after_entry"]+=1
        item["last_t"]=int(b["t"])
        item["equity_usd"]=round(item["units"]*price*(1-COST),5)
        item["estimated_net_pct"]=round(100*(item["equity_usd"]/CAPITAL-1),4)
        if item["observations_after_entry"]>=item["horizon_days"]:
            item["status"]="completed_unvalidated_paper_trial"
            outcomes.append({"asset":item["asset"],"id":item["id"],
                             "status":item["status"],"estimated_net_pct":item["estimated_net_pct"]})
    report={
        "schema":1,"generated_at":now.isoformat(),"type":"independent_forward_only_paper_scenarios",
        "active":sum(x.get("status") in ("waiting_next_closed_day","in_paper_position") for x in trials),
        "trials":trials[-12:],"events":outcomes,
        "controls":{"max_simulated_capital_usd":CAPITAL,"paper_only":True,
                    "real_orders":False,"prediction_guaranteed":False,
                    "sampled_whale_transfer_is_confirmed_buy":False},
        "warning":"Paper fills at later observed daily closes, not executable exchange fills. Model proposals are hypotheses, not proven profits.",
    }
    return report,{"schema":1,"trials":trials[-12:]}


def main():
    now=datetime.now(timezone.utc)
    report,state=evolve(now,read(IDEAS),read(PULSE),read(CANDLES),read(STATE))
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Independent Gemini placement studies",len(report["trials"]),
          "active",report["active"],"new events",len(report["events"]))


if __name__=="__main__":
    main()
