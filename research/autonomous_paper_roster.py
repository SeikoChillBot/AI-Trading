"""Autonomous reversible paper research roster; never edits original 36 robots.

Promotion requires independently qualified paper champions from competition.
Original historical identities, portfolios and Hold benchmarks are immutable.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROBOT_REPORT=ROOT/"reports/robot_evolution.json"
COMPETITION=ROOT/"reports/strategy_competition.json"
STATE=ROOT/"state/autonomous_paper_roster.json"
REPORT=ROOT/"reports/autonomous_paper_roster.json"
MAX_ACTIVE=12

def load(path):
    try:
        x=json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {}
    except (OSError,ValueError):
        return {}

def build(now,robots,competition,previous):
    if (robots.get("schema")!=1 or len(robots.get("robots",[]))!=36
        or robots.get("real_orders") is not False
        or competition.get("schema")!=1 or competition.get("real_orders") is not False
        or competition.get("robots_modified") is not False):
        raise ValueError("unverified_roster_sources")
    all_robots=robots["robots"]
    if len({x.get("strategy") for x in all_robots})!=36:
        raise ValueError("duplicate_original_robot")
    if sum(x.get("role")=="immutable_hold_benchmark" for x in all_robots)!=12:
        raise ValueError("hold_benchmarks_changed")
    ranked=competition.get("ranked",[])
    if not isinstance(ranked,list):
        raise ValueError("invalid_competition")
    champions={}
    for row in ranked:
        if not isinstance(row,dict):
            continue
        key=row.get("id")
        if (isinstance(key,str) and row.get("stage")=="paper_champion"
            and row.get("history_checks_pass") is True
            and row.get("real_orders") is False
            and type(row.get("observed_days")) is int and row["observed_days"]>=120
            and type(row.get("closed_trades")) is int and row["closed_trades"]>=12
            and type(row.get("consecutive_qualified_days")) is int
            and row["consecutive_qualified_days"]>=14
            and isinstance(row.get("net_pct"),(int,float)) and row["net_pct"]>=2
            and isinstance(row.get("excess_vs_hold_points"),(int,float))
            and row["excess_vs_hold_points"]>0
            and isinstance(row.get("drawdown_pct"),(int,float))
            and 0<=row["drawdown_pct"]<=10):
            champions[key]=row
    old=previous.get("active",[]) if isinstance(previous,dict) else []
    old=old if isinstance(old,list) else []
    active=[x for x in old if isinstance(x,str) and x in champions][:MAX_ACTIVE]
    events=previous.get("events",[]) if isinstance(previous,dict) else []
    events=[x for x in events if isinstance(x,dict)][-180:]
    for key in old:
        if isinstance(key,str) and key not in active:
            events.append({"at":now.isoformat(),"action":"paper_candidate_revoked",
                           "candidate":key,"reason":"champion_evidence_lost"})
    for row in ranked:
        key=row.get("id") if isinstance(row,dict) else None
        if key in champions and key not in active and len(active)<MAX_ACTIVE:
            active.append(key)
            events.append({"at":now.isoformat(),"action":"paper_candidate_activated",
                           "candidate":key,"reason":"prospective_paper_champion",
                           "net_pct":row.get("net_pct"),"excess_vs_hold_points":row.get("excess_vs_hold_points")})
    events=events[-180:]
    legacy=[{"id":r["strategy"],"role":r["role"],
             "status":"immutable_hold" if r["role"]=="immutable_hold_benchmark"
             else "legacy_reference_retained",
             "historical_net_pct":r.get("paper_return_pct")}
            for r in all_robots]
    report={"schema":1,"generated_at":now.isoformat(),
            "mode":"autonomous_independent_paper_research_roster",
            "active_candidate_ids":active,
            "active_candidate_count":len(active),
            "historical_robots":legacy,
            "archived_candidates":[e for e in events if e.get("action")=="paper_candidate_revoked"],
            "events":events[-60:],
            "legacy_robots_modified":False,"real_orders":False,
            "warning":"Research roster only; no original robot retired, no broker execution, no profit guaranteed."}
    state={"schema":1,"active":active,"events":events,"real_orders":False}
    return report,state

def main():
    now=datetime.now(timezone.utc)
    report,state=build(now,load(ROBOT_REPORT),load(COMPETITION),load(STATE))
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    STATE.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Autonomous paper research roster:",report["active_candidate_count"])

if __name__=="__main__":
    main()
