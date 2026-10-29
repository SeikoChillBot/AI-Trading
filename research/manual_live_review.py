"""Manual-only review gate for a possible FUTURE tiny live experiment.

No broker, wallet, API keys, orders, approval fields or trading commands.
Even a passing research screen is only an invitation to a human risk review,
never authorization to trade or a prediction of profitability.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "reports/strategy_forward.json"
FOUNDRY = ROOT / "state/strategy_knowledge_base.json"
REPORT = ROOT / "reports/manual_live_review.json"

MIN_NEW_DAYS = 90
MIN_CLOSED_TRADES = 10
MAX_PAPER_DRAWDOWN_PCT = 10.0
MIN_NET_PCT = 2.0


def read(path):
    try:
        x = json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def valid_num(x):
    try:
        n = float(x)
        return n if not isinstance(x, bool) and math.isfinite(n) else None
    except (ValueError, TypeError, OverflowError):
        return None


def build(now, forward, foundry_memory):
    records = forward.get("trials", []) if isinstance(forward, dict) else []
    ideas = foundry_memory.get("ideas", []) if isinstance(foundry_memory, dict) else []
    records = records if isinstance(records, list) else []
    ideas = ideas if isinstance(ideas, list) else []
    verified = {}
    for raw in ideas:
        if not isinstance(raw, dict) or not isinstance(raw.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(raw["spec"])
            if raw.get("id") == foundry.identifier(spec):
                verified[raw["id"]] = raw
        except (ValueError, KeyError, TypeError):
            continue
    results = []
    try:
        generated = datetime.fromisoformat(str(forward.get("generated_at", "")).replace("Z", "+00:00"))
        fresh = (generated.tzinfo is not None
                 and 0 <= (now - generated).total_seconds() <= 12 * 3600)
    except (TypeError, ValueError, OverflowError):
        fresh = False
    valid_report = (isinstance(forward, dict)
                    and forward.get("schema") == 1
                    and forward.get("real_orders") is False
                    and forward.get("robots_modified") is False
                    and fresh)
    for row in records[:24] if valid_report else []:
        if not isinstance(row, dict) or row.get("id") not in verified:
            continue
        identity = row["id"]
        evidence = verified[identity].get("latest_result", {})
        checks = evidence.get("checks", {}) if isinstance(evidence, dict) else {}
        if not isinstance(checks, dict):
            checks = {}
        days = row.get("observed_days")
        count = row.get("closed_trades")
        net = valid_num(row.get("net_pct"))
        excess = valid_num(row.get("excess_vs_hold_points"))
        dd = valid_num(row.get("max_drawdown_pct"))
        block = []
        if row.get("status") != "observing_paper_only":
            block.append("prospective_paper_observation_not_active")
        if type(days) is not int or days < MIN_NEW_DAYS:
            block.append("not_enough_new_observed_days")
        if type(count) is not int or count < MIN_CLOSED_TRADES:
            block.append("not_enough_closed_trades")
        if net is None or net < MIN_NET_PCT:
            block.append("positive_net_after_fees_not_demonstrated")
        if excess is None or excess <= 0:
            block.append("no_prospective_advantage_over_hold")
        if dd is None or dd < 0 or dd > MAX_PAPER_DRAWDOWN_PCT:
            block.append("drawdown_too_high_or_unknown")
        if evidence.get("evidence_kind") != "exploratory_historical_replay_not_blind_oos":
            block.append("historical_evidence_unavailable")
        if not all(checks.get(k) is True for k in
                   ("enough_closed_trades", "positive_average_net",
                    "positive_with_double_costs", "beats_hold_in_most_folds",
                    "drawdown_under_20_pct")):
            block.append("historical_stress_checks_not_passed")
        results.append({
            "id": identity, "asset": verified[identity]["spec"]["asset"],
            "status": "eligible_for_human_risk_review_only" if not block
                      else "research_in_progress",
            "blockers": block,
            "observed_days": days, "closed_trades": count,
            "net_after_fees_pct": net, "excess_vs_hold_points": excess,
            "drawdown_pct": dd, "live_approved": False,
            "can_place_real_orders": False,
        })
    return {
        "schema": 1, "generated_at": now.isoformat(),
        "tracked_research_candidates": len(results),
        "eligible_for_human_review": sum(not x["blockers"] for x in results),
        "trials": results,
        "real_trading_enabled": False,
        "exchange_connected": False, "model_can_enable_live_trading": False,
        "requires_explicit_user_approval": True,
        "additional_real_trial_requirements": [
            "verify_broker_and_order_minimums",
            "independent_execution_slippage_audit",
            "risk_budget_and_absolute_loss_cap",
            "order_and_reconciliation_tests",
            "emergency_kill_switch",
            "human_approved_small_capital_and_venue",
        ],
        "warning": "Research success can fail out of sample. Nothing here authorizes live trading.",
    }


def main():
    report = build(datetime.now(timezone.utc), read(FORWARD), read(FOUNDRY))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Manual-only live review:", report["eligible_for_human_review"],
          "ready for risk discussion,", report["tracked_research_candidates"], "tracked")


if __name__ == "__main__":
    main()
