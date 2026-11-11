"""Read-only, evidence-gated lifecycle recommendations for Seiko Lab.

This module never changes portfolio, robot, Hold, or forward-trial state.
"""
from __future__ import annotations

from datetime import datetime, timezone

MIN_DAYS = 30
MIN_CLOSED_TRADES = 20
MAX_DRAWDOWN_PCT = 15.0
MIN_EXCESS_VS_HOLD_POINTS = 2.0


def evaluate(robots, forward, generated_at=None):
    """Classify candidates without equating historic losses with permanent failure."""
    if not isinstance(robots, list) or not isinstance(forward, dict):
        raise ValueError("invalid_lifecycle_inputs")
    trials = forward.get("trials", [])
    if not isinstance(trials, list):
        raise ValueError("invalid_forward_trials")
    result = []
    for robot in robots:
        if not isinstance(robot, dict) or not isinstance(robot.get("strategy"), str):
            continue
        hold = robot.get("role") == "immutable_hold_benchmark"
        try:
            net = float(robot["paper_return_pct"])
            dd = float(robot["drawdown_pct"])
            trades = int(robot["closed_roundtrips"])
        except (TypeError, ValueError, KeyError):
            net = dd = None
            trades = 0
        review = not hold and net is not None and dd is not None and (
            net <= -30 and dd >= 30 and trades >= 20)
        result.append({
            "robot": robot["strategy"],
            "role": robot.get("role"),
            "decision": "immutable_benchmark" if hold else
                        "review_for_retirement" if review else "continue_observation",
            "historical_net_pct": net,
            "historical_drawdown_pct": dd,
            "historical_closed_trades": trades,
            "archived": False,
            "replaced_by": None,
            "reason": "historical_losses_trigger_review_not_proof" if review else
                      "benchmark_immutable" if hold else "insufficient_retirement_evidence",
        })
    proposals = []
    for trial in trials:
        if not isinstance(trial, dict) or not isinstance(trial.get("id"), str):
            continue
        try:
            days = int(trial["observed_days"])
            trades = int(trial["closed_trades"])
            net = float(trial["net_pct"])
            excess = float(trial["excess_vs_hold_points"])
            dd = float(trial["max_drawdown_pct"])
        except (ValueError, TypeError, KeyError):
            days = trades = 0
            net = excess = dd = None
        checks = {
            "minimum_days": days >= MIN_DAYS,
            "minimum_closed_trades": trades >= MIN_CLOSED_TRADES,
            "positive_net_after_costs": net is not None and net > 0,
            "excess_vs_hold": excess is not None and excess >= MIN_EXCESS_VS_HOLD_POINTS,
            "bounded_drawdown": dd is not None and 0 <= dd <= MAX_DRAWDOWN_PCT,
            # Not available in the current summary: never infer it from net return.
            "double_fees_resilience": False,
            "paired_market_regimes": False,
            "independent_execution_audit": False,
        }
        proposals.append({
            "id": trial["id"], "source": trial.get("source"),
            "asset": trial.get("asset"), "logic": trial.get("logic"),
            "observed_days": days, "closed_trades": trades,
            "net_pct": net, "excess_vs_hold_points": excess,
            "drawdown_pct": dd,
            "checks": checks, "qualified": all(checks.values()),
            "decision": "continue_prospective_testing",
            "reason": "prospective_evidence_incomplete",
        })
    return {
        "schema": 1,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "source": "deterministic_read_only_lifecycle_review",
        "robots": result, "candidate_trials": proposals,
        "retirement_reviews": sum(x["decision"] == "review_for_retirement" for x in result),
        "qualified_replacements": 0,
        "automatic_archivals": 0, "automatic_promotions": 0,
        "real_orders": False, "historical_robots_modified": False,
        "warning": "No strategy can be proved unable to recover. Review is not retirement; future replacement requires independent prospective proof.",
    }
