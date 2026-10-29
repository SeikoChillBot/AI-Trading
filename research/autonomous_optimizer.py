"""Autonomous research-only parameter search for AIT.

Finite grid, no LLM code, no wallet or brokerage API. Selection uses only an
earlier development period; a later historical period is assessed *after*
selection. Neither is called a pristine holdout: existing AIT research has
already examined historical markets. All candidates are paper-only.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
CANDLES = ROOT / "reports/challenger_candles.json"
STATE = ROOT / "state/autonomous_optimizer.json"
REPORT = ROOT / "reports/autonomous_optimizer.json"
ASSETS = foundry.ASSETS
DEVELOPMENT_FOLDS = 4
CHALLENGE_FOLDS = 2
FOLD_DAYS = 60
SEARCH_EVERY_CLOSED_DAYS = 7
MAX_STORED = 36
MAX_PER_ASSET = 1
RATIONALE = (
    "Recherche déterministe hors argent réel : tester une logique de marché "
    "figée après sélection chronologique et comparer les résultats au témoin."
)


def grid(asset):
    for logic, window, threshold, horizon in product(
        foundry.LOGICS, foundry.WINDOWS, (0.5, 1, 2), foundry.MAX_HOLD
    ):
        yield foundry.normalise({
            "asset": asset, "logic": logic, "lookback_days": window,
            "threshold_pct": threshold, "max_hold_days": horizon,
            "rationale": RATIONALE,
        })


def score_development(bars, spec):
    """Never read the last CHALLENGE_FOLDS*FOLD_DAYS price observations."""
    end_dev = len(bars) - CHALLENGE_FOLDS * FOLD_DAYS
    start_dev = end_dev - DEVELOPMENT_FOLDS * FOLD_DAYS
    if start_dev < 42:
        raise ValueError("not_enough_development_data")
    folds = []
    for a in range(start_dev, end_dev, FOLD_DAYS):
        end = a + FOLD_DAYS
        nominal = foundry.replay(bars, spec, a, end)
        stressed = foundry.replay(bars, spec, a, end, fee=foundry.COST * 2)
        witness = foundry.benchmark(bars, a, end)
        folds.append({
            "net": nominal["net_pct"],
            "stress": stressed["net_pct"],
            "excess": nominal["net_pct"] - witness,
            "drawdown": nominal["drawdown_pct"],
            "trades": nominal["closed_trades"],
        })
    mean = lambda key: sum(row[key] for row in folds) / len(folds)
    worst = max(row["drawdown"] for row in folds)
    trades = sum(row["trades"] for row in folds)
    # Strong penalties for losses under doubled costs and downside.
    value = (mean("net") + min(0.0, mean("stress")) * 1.2
             + mean("excess") * .25 - worst * .35)
    if trades < 4:
        value -= 6
    return {
        "score": round(value, 5),
        "avg_net_pct": round(mean("net"), 5),
        "avg_double_cost_net_pct": round(mean("stress"), 5),
        "avg_excess_vs_hold_points": round(mean("excess"), 5),
        "max_drawdown_pct": round(worst, 5),
        "closed_trades": trades,
        "positive_folds": sum(row["net"] > 0 for row in folds),
        "beating_hold_folds": sum(row["excess"] > 0 for row in folds),
        "fold_count": len(folds),
        "selection_window": "four_preceding_60_day_folds_only",
    }


def challenge(bars, spec):
    """Read ONLY after the candidate has been selected on earlier folds."""
    start = len(bars) - CHALLENGE_FOLDS * FOLD_DAYS
    folds = []
    for a in range(start, len(bars), FOLD_DAYS):
        result = foundry.replay(bars, spec, a, a + FOLD_DAYS)
        stressed = foundry.replay(bars, spec, a, a + FOLD_DAYS,
                                  fee=foundry.COST * 2)
        witness = foundry.benchmark(bars, a, a + FOLD_DAYS)
        folds.append({
            "net_pct": result["net_pct"],
            "double_cost_net_pct": stressed["net_pct"],
            "excess_vs_hold_points": round(result["net_pct"] - witness, 5),
            "drawdown_pct": result["drawdown_pct"],
            "closed_trades": result["closed_trades"],
        })
    return {
        "period": "reused_historical_challenge_not_pristine_oos",
        "folds": folds,
        "net_average_pct": round(sum(x["net_pct"] for x in folds) / len(folds), 5),
        "both_positive_after_costs": all(x["net_pct"] > 0 for x in folds),
        "positive_double_costs": all(x["double_cost_net_pct"] > 0 for x in folds),
        "beats_hold_both": all(x["excess_vs_hold_points"] > 0 for x in folds),
    }


def optimise_asset(bars, asset, now):
    foundry.validate_bars(bars, now)
    ranked = []
    for spec in grid(asset):
        metrics = score_development(bars, spec)
        ranked.append((metrics["score"], foundry.identifier(spec), spec, metrics))
    # Same input => same selection, no random search or optimistic resampling.
    best = sorted(ranked, key=lambda row: (-row[0], row[1]))[0]
    _, identifier, spec, metrics = best
    later = challenge(bars, spec)
    return {
        "id": identifier, "spec": spec,
        "selection_metrics": metrics,
        "historical_challenge": later,
        "grid_evaluated": len(ranked),
        "frozen_at_closed_day": bars[-1]["t"],
        "source": "autonomous_grid_search",
        "historical_candidate_only": True,
        "eligible_for_live_trading": False,
        "eligible_for_robot_promotion": False,
        "prospective_data_required": True,
    }


def build(now, candles, prior):
    previous = prior.get("candidates", []) if isinstance(prior, dict) else []
    previous = previous if isinstance(previous, list) else []
    known = {}
    for item in previous[-MAX_STORED:]:
        if not isinstance(item, dict) or not isinstance(item.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(item["spec"])
            key = foundry.identifier(spec)
        except (ValueError, TypeError, KeyError):
            continue
        if item.get("id") == key:
            known[key] = item
    issues = {}
    new = []
    searched = set()
    latest = {}
    source = candles if isinstance(candles, dict) else {}
    for asset in ASSETS:
        bars = source.get(asset, [])
        try:
            foundry.validate_bars(bars, now)
            last_t = bars[-1]["t"]
            last_search = prior.get("last_search_closed_day", {}).get(asset)
            # Do not optimize again every 2 hours on nearly identical data.
            due = (type(last_search) is not int
                   or last_t - last_search >= SEARCH_EVERY_CLOSED_DAYS * 86400)
            if due:
                candidate = optimise_asset(bars, asset, now)
                searched.add(asset)
                candidate["created_at"] = now.isoformat()
                key = candidate["id"]
                if key not in known:
                    known[key] = candidate
                    new.append(key)
                latest[asset] = key
            else:
                previous_best = prior.get("latest_by_asset", {}).get(asset)
                if previous_best in known:
                    latest[asset] = previous_best
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            issues[asset] = str(exc)[:65]
            previous_best = prior.get("latest_by_asset", {}).get(asset)
            if previous_best in known:
                latest[asset] = previous_best
    ordered = list(known.values())[-MAX_STORED:]
    retained = {c["id"]: c for c in ordered}
    latest = {k: v for k, v in latest.items() if v in retained}
    last_search = dict(prior.get("last_search_closed_day", {})) if isinstance(
        prior.get("last_search_closed_day", {}), dict) else {}
    for asset in searched:
        last_search[asset] = source[asset][-1]["t"]
    state = {
        "schema": 1, "updated_at": now.isoformat(),
        "candidates": ordered, "latest_by_asset": latest,
        "last_search_closed_day": last_search,
        "real_orders": False, "robot_changes": False,
    }
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "source": "autonomous_grid_search",
        "real_orders": False, "robot_changes": False,
        "selection_uses_future_challenge_data": False,
        "candidate_count": len(ordered), "new_candidate_ids": new,
        "latest_by_asset": latest,
        "candidates": ordered[-MAX_STORED:],
        "issues": issues,
        "research_goal": "maximize_risk_adjusted_net_return_not_win_rate",
        "next_stage": "independent_future_paper_trials_only",
        "warning": "Multiple comparisons and reused history can overfit; no guaranteed profits or live eligibility.",
    }
    return report, state


def main():
    now = datetime.now(timezone.utc)
    report, state = build(now, foundry.read(CANDLES), foundry.read(STATE))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Autonomous research optimizer:", report["candidate_count"],
          "total candidates,", len(report["new_candidate_ids"]), "new",
          "issues:", len(report["issues"]))


if __name__ == "__main__":
    main()
