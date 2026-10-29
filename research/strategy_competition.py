"""Conservative AIT paper-only competition: progress, drift and revocation.

Prospective paper performance must advance on a NEW observed daily candle.
No automatic strategy promotion to the original 36 robots, no live execution.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
FORWARD_STATE = ROOT / "state/strategy_forward_positions.json"
KNOWLEDGE = ROOT / "state/strategy_knowledge_base.json"
STATE = ROOT / "state/strategy_competition.json"
REPORT = ROOT / "reports/strategy_competition.json"
MIN_DAYS = 120
MIN_TRADES = 12
MIN_PASS_NEW_DAYS = 14
MAX_DRAWDOWN = 10.
MAX_HISTORY = 150


def read(path):
    try:
        x = json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def finite(x):
    try:
        value = float(x)
        return value if not isinstance(x, bool) and math.isfinite(value) else None
    except (ValueError, TypeError, OverflowError):
        return None


def build(now, forward, knowledge, previous):
    prior = previous if isinstance(previous, dict) else {}
    trails = prior.get("trails", {})
    trails = trails if isinstance(trails, dict) else {}
    tracks = forward.get("tracks", {}) if isinstance(forward, dict) else {}
    records = knowledge.get("ideas", []) if isinstance(knowledge, dict) else []
    allowed = {}
    for x in records if isinstance(records, list) else []:
        if not isinstance(x, dict) or not isinstance(x.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(x["spec"])
            if x.get("id") == foundry.identifier(spec):
                allowed[x["id"]] = x
        except (ValueError, KeyError, TypeError):
            continue
    if (not isinstance(forward, dict) or forward.get("schema") != 1
            or forward.get("real_orders") is not False
            or not isinstance(tracks, dict)
            or (not isinstance(knowledge, dict)
                or knowledge.get("real_orders") is not False)):
        return ({
            "schema": 1, "generated_at": now.isoformat(), "state": "unavailable",
            "paper_champions": 0, "ranked": [],
            "real_orders": False, "robots_modified": False
        }, {"schema": 1, "trails": trails, "real_orders": False})
    rankings = []
    updated = {}
    for key, row in list(tracks.items())[:24]:
        if key not in allowed or not isinstance(row, dict):
            continue
        idea = allowed[key]
        try:
            spec = foundry.normalise(row["spec"])
            if foundry.identifier(spec) != key:
                continue
        except (ValueError, KeyError, TypeError):
            continue
        history = idea.get("latest_result", {})
        checks = history.get("checks", {}) if isinstance(history, dict) else {}
        hist_ok = (isinstance(checks, dict) and
                   all(checks.get(field) is True for field in (
                       "enough_closed_trades", "positive_average_net",
                       "positive_with_double_costs", "beats_hold_in_most_folds",
                       "drawdown_under_20_pct")))
        net = finite(row.get("net_pct"))
        excess = finite(row.get("excess_vs_hold_points"))
        dd = finite(row.get("max_drawdown_pct"))
        day = row.get("last_t")
        days = row.get("observed_days")
        closed = row.get("closed_trades")
        healthy = (
            row.get("status") == "observing_paper_only"
            and type(days) is int and days >= MIN_DAYS
            and type(closed) is int and closed >= MIN_TRADES
            and net is not None and net >= 2
            and excess is not None and excess > 0
            and dd is not None and 0 <= dd <= MAX_DRAWDOWN
            and hist_ok
        )
        earlier = trails.get(key, {})
        earlier = earlier if isinstance(earlier, dict) else {}
        past_history = earlier.get("daily_snapshots", [])
        past_history = past_history[-MAX_HISTORY:] if isinstance(past_history, list) else []
        consecutive = int(earlier.get("consecutive_qualified_days", 0))
        last = earlier.get("last_observed_t")
        if type(day) is int and type(days) is int and days > 0 and day != last:
            if last is not None and (type(last) is not int or day - last != 86400):
                consecutive = 0
            consecutive = consecutive + 1 if healthy else 0
            past_history.append({
                "t": day, "observed_days": days,
                "net_pct": net, "excess_vs_hold_points": excess,
                "max_drawdown_pct": dd, "healthy": healthy,
            })
            past_history = past_history[-MAX_HISTORY:]
        # Persist state of achievement but revoke instantly upon a new loss
        # of criteria. Existing trail from an older day is not enough.
        previous_stage = earlier.get("stage")
        stage = ("paper_champion" if healthy and consecutive >= MIN_PASS_NEW_DAYS
                 else "qualifying_paper_candidate" if healthy
                 else "paper_observing" if type(days) is int and days > 0
                 else "awaiting_prospective_evidence")
        if previous_stage == "paper_champion" and stage != "paper_champion":
            stage = "paper_champion_revoked"
        next_trail = {
            "last_observed_t": day if type(day) is int else last,
            "consecutive_qualified_days": consecutive,
            "stage": stage, "daily_snapshots": past_history,
        }
        updated[key] = next_trail
        # Sorting is descriptive, not candidate selection. Require positive
        # forward excess before calling a strategy a paper champion.
        score = (net + .3 * excess - .5 * dd) if all(
            value is not None for value in (net, excess, dd)) else None
        rankings.append({
            "id": key, "asset": spec["asset"], "logic": spec["logic"],
            "source": idea.get("source"),
            "observed_days": days if type(days) is int else 0,
            "closed_trades": closed if type(closed) is int else 0,
            "net_pct": net, "excess_vs_hold_points": excess,
            "drawdown_pct": dd, "score": round(score, 4) if score is not None else None,
            "stage": stage, "consecutive_qualified_days": consecutive,
            "history_checks_pass": hist_ok,
            "real_orders": False,
        })
    rankings.sort(key=lambda x: (
        x["stage"] != "paper_champion",
        x["score"] is None,
        -(x["score"] if x["score"] is not None else -1e6),
        x["id"],
    ))
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "state": "observing_prospective_paper",
        "ranked": rankings,
        "tracked": len(rankings),
        "paper_champions": sum(x["stage"] == "paper_champion" for x in rankings),
        "qualifying_candidates": sum(x["stage"] == "qualifying_paper_candidate" for x in rankings),
        "real_orders": False, "robots_modified": False,
        "original_robots_promoted": 0,
        "warning": "A paper champion is not verified profit nor a mandate for real trading.",
    }
    state = {"schema": 1, "updated_at": now.isoformat(),
             "trails": updated, "real_orders": False}
    return report, state


def main():
    now = datetime.now(timezone.utc)
    report, state = build(now, read(FORWARD_STATE), read(KNOWLEDGE), read(STATE))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Paper strategy competition:", report.get("tracked", 0),
          "tracked,", report["paper_champions"], "champions")


if __name__ == "__main__":
    main()
