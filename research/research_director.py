"""AIT experimental director: plan -> freeze -> prospective test -> revise.

Reads hypotheses proposed by Gemini's existing free-tier call and a bounded,
explicitly labelled local fallback. Unlike a replay optimizer, each experiment
has a falsifiable question, a rationale, a rejection rule and a prospective
checkpoint. No code execution from the model, no real orders, no robot edits.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
CANDLES = ROOT / "reports/challenger_candles.json"
KNOWLEDGE = ROOT / "state/strategy_knowledge_base.json"
SCIENCE = ROOT / "reports/scientific_memory.json"
SCIENCE_STATE = ROOT / "state/scientific_memory.json"
PROPOSALS = ROOT / "reports/ai_research_proposals.json"
FORWARD = ROOT / "state/strategy_forward_positions.json"
STATE = ROOT / "state/research_director.json"
REPORT = ROOT / "reports/research_director.json"
MAX_EXPERIMENTS = 100
MAX_ATTEMPTED = 3500
MIN_OBSERVED_DAYS = 90
MIN_CLOSED_TRADES = 10

GOALS = {
    "cost_resilience": ("positive_with_double_costs",
        "Les frais simulés peuvent annuler les signaux; tester des filtres d'entrée.",
        "Une stratégie ne valide pas sa robustesse si ses performances futures nettes sont négatives."),
    "trade_frequency": ("enough_closed_trades",
        "Une stratégie trop restrictive peut produire un échantillon insuffisant.",
        "Rejeter toute conclusion de qualité tant que le nombre de transactions reste insuffisant."),
    "beat_hold": ("beats_hold_in_most_folds",
        "Un filtre de tendance pourrait, ou non, améliorer le témoin Hold.",
        "Rejeter la supériorité si le rendement futur net ne dépasse pas le témoin."),
    "net_return": ("positive_average_net",
        "Comparer un signal conditionnel à une règle simple après frais.",
        "Rejeter la rentabilité si le rendement prospectif net est négatif."),
    "risk_control": ("drawdown_under_20_pct",
        "Tester un filtre de volatilité pour limiter les expositions mal adaptées.",
        "Rejeter si les pertes prospectives ou le drawdown dépassent les bornes."),
}
# All choices are finite recipes, not LLM-created programs. The objective,
# choice and outcome are persisted for scientific auditing.
RECIPES = {
    "cost_resilience": [
        ("ema_trend", 20, 1, 7, ["ema_uptrend", "quiet_volatility"]),
        ("breakout", 40, 2, 7, ["ema_uptrend", "positive_momentum"]),
        ("dual_confirmation", 40, 2, 7, ["quiet_volatility"]),
    ],
    "trade_frequency": [
        ("mean_reversion", 10, .5, 1, []),
        ("rsi_reversal", 10, .5, 1, []),
        ("trend_following", 10, .5, 3, ["positive_momentum"]),
    ],
    "beat_hold": [
        ("ema_trend", 40, .5, 7, ["ema_uptrend"]),
        ("breakout", 20, 1, 7, ["positive_momentum"]),
        ("dual_confirmation", 20, .5, 7, ["rsi_strength", "ema_uptrend"]),
    ],
    "net_return": [
        ("rsi_reversal", 20, 1, 3, ["rsi_oversold"]),
        ("mean_reversion", 20, 1, 3, ["quiet_volatility"]),
        ("ema_trend", 20, 1, 7, ["rsi_strength"]),
    ],
    "risk_control": [
        ("volatility_gate", 20, 1, 3, ["quiet_volatility"]),
        ("dual_confirmation", 20, 1, 3, ["quiet_volatility", "positive_momentum"]),
        ("ema_trend", 40, 1, 3, ["quiet_volatility"]),
    ],
}


def read(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _checked_plan(raw, asset):
    if not isinstance(raw, dict) or raw.get("asset") != asset:
        raise ValueError("wrong_asset")
    goal = raw.get("goal")
    if goal not in GOALS:
        raise ValueError("goal_not_supported")
    question = raw.get("hypothesis")
    rejection = raw.get("rejection_rule")
    if (not isinstance(question, str) or not 15 <= len(question.strip()) <= 350
            or not isinstance(rejection, str) or not 15 <= len(rejection.strip()) <= 350):
        raise ValueError("unfalsifiable_plan")
    spec = foundry.normalise(raw.get("strategy"))
    if spec["asset"] != asset:
        raise ValueError("strategy_asset_mismatch")
    return goal, question.strip(), rejection.strip(), spec


def prospective_status(record, forward):
    """Never treat historical replays or unchanged candles as future validation."""
    if not isinstance(record, dict) or not isinstance(forward, dict):
        return "awaiting_prospective_data", 0
    rec = forward.get("tracks", {}).get(record.get("id"), {})
    if not isinstance(rec, dict) or rec.get("id") != record.get("id"):
        return "awaiting_prospective_data", 0
    try:
        if foundry.identifier(foundry.normalise(rec["spec"])) != record["id"]:
            return "invalid_forward_provenance", 0
    except (ValueError, TypeError, KeyError):
        return "invalid_forward_provenance", 0
    days = rec.get("observed_days", 0)
    trades = rec.get("closed_trades", 0)
    # Never use a self-reported observation count without matching genuine
    # successive *future* calendar time after this plan was registered.
    frozen_day = record.get("closed_day_at_registration")
    last_day = rec.get("last_t")
    chronological = (
        type(frozen_day) is int and type(last_day) is int
        and last_day > frozen_day
        and type(days) is int and 0 <= days <= (last_day - frozen_day) // 86400
        and (last_day - frozen_day) % 86400 == 0
    )
    if (not chronological or type(trades) is not int or
            days < MIN_OBSERVED_DAYS or trades < MIN_CLOSED_TRADES or
            rec.get("status") != "observing_paper_only"):
        return "awaiting_prospective_data", max(0, days) if type(days) is int else 0
    net, excess, dd = (rec.get("net_pct"), rec.get("excess_vs_hold_points"),
                       rec.get("max_drawdown_pct"))
    if (any(type(v) not in (int, float) for v in (net, excess, dd))
            or not all(-10000 < v < 10000 for v in (net, excess, dd))):
        return "invalid_forward_metrics", days
    if net <= 0 or excess <= 0 or dd > 20:
        return "prospectively_contradicted", days
    # Still only exploratory: repeated longer studies & controls are required.
    return "tentatively_supported_paper_only", days


def _eligible_model_tasks(proposals, now):
    if (not isinstance(proposals, dict)
            or proposals.get("state") != "model_reflection_completed"
            or proposals.get("source") != "gemini_generate_content"
            or proposals.get("provider") != "gemini"
            or proposals.get("real_orders_enabled") is not False
            or proposals.get("live_strategy_changes_enabled") is not False):
        return []
    # No need to make extra model calls. The main Gemini request supplies the
    # proposals and still respects its free-tier six-hour quota.
    time_text = proposals.get("model_last_called_at")
    try:
        called = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
        if called.tzinfo is None or not 0 <= (now-called).total_seconds() <= 86400:
            return []
    except (ValueError, AttributeError, TypeError):
        return []
    tasks = proposals.get("research_tasks", [])
    return tasks[:2] if isinstance(tasks, list) else []


def _local_plan(asset, goal, tried):
    for logic, window, threshold, hold, gates in RECIPES[goal]:
        raw = {"asset": asset, "logic": logic, "lookback_days": window,
               "threshold_pct": threshold, "max_hold_days": hold,
               "confirmations": gates,
               "rationale": GOALS[goal][1]}
        spec = foundry.normalise(raw)
        if foundry.identifier(spec) not in tried:
            return spec
    return None


def build(now, candles, science, science_state, proposals, knowledge, forward, previous):
    prior = previous if isinstance(previous, dict) else {}
    archive = [x for x in prior.get("experiments", [])
               if isinstance(x, dict) and isinstance(x.get("id"), str)]
    archive = archive[-MAX_EXPERIMENTS:]
    attempted = [x for x in prior.get("attempted_ids", [])
                 if isinstance(x, str) and len(x) == 18]
    already = set(attempted)
    if isinstance(science_state, dict):
        seen = science_state.get("seen_spec_ids", [])
        if isinstance(seen, list):
            already.update(x for x in seen if isinstance(x, str) and len(x) == 18)
    if isinstance(knowledge, dict):
        rows = knowledge.get("ideas", [])
        if isinstance(rows, list):
            already.update(x.get("id") for x in rows if isinstance(x, dict))
    active = prior.get("active_by_asset", {})
    active = active if isinstance(active, dict) else {}
    previous_active = {asset: active.get(asset) for asset in foundry.ASSETS}
    by_id = {row["id"]: row for row in archive}
    status, selections, errors, evidence_days = {}, {}, {}, {}
    science_ok = (isinstance(science, dict)
                  and science.get("schema") == 1
                  and science.get("state") == "research_memory_recorded"
                  and science.get("real_orders") is False
                  and science.get("no_causal_attribution") is True
                  and science.get("no_promotions") is True)
    agenda = science.get("research_agenda", []) if science_ok else []
    agenda = agenda if isinstance(agenda, list) else []
    # Rotate goals across assets to avoid every bot repeating one idea.
    goal_order = []
    mapping = {"cost_sensitivity": "cost_resilience",
               "trade_density": "trade_frequency",
               "hold_comparison": "beat_hold",
               "net_return": "net_return",
               "drawdown": "risk_control"}
    for row in agenda:
        if isinstance(row, dict) and row.get("category") in mapping:
            goal = mapping[row["category"]]
            if goal not in goal_order:
                goal_order.append(goal)
    goal_order += [g for g in GOALS if g not in goal_order]
    tasks = _eligible_model_tasks(proposals, now)
    model_used = 0
    local_used = 0
    for position, asset in enumerate(foundry.ASSETS):
        bars = candles.get(asset) if isinstance(candles, dict) else None
        try:
            if (not science_ok or not isinstance(science_state, dict)
                    or science_state.get("real_orders") is not False
                    or science_state.get("robots_modified") is not False):
                raise ValueError("unverified_scientific_evidence")
            foundry.validate_bars(bars, now)
            last_t = bars[-1]["t"]
            old_id = previous_active.get(asset)
            old = by_id.get(old_id)
            if old:
                situation, days = prospective_status(old, forward)
                old["prospective_status"] = situation
                old["prospective_observed_days"] = days
                evidence_days[asset] = days
                if situation == "awaiting_prospective_data":
                    selections[asset] = old_id
                    status[asset] = situation
                    continue
                # Both strong and weak completed *prospective* experiments
                # open a new distinct question. Keep the old frozen experiment
                # in the archive: the league, not this director, decides which
                # positive paper strategies deserve continuing observation.
            targets = goal_order[position:] + goal_order[:position]
            chosen = None
            for plan in tasks:
                if not isinstance(plan, dict) or plan.get("asset") != asset:
                    continue
                try:
                    goal, question, reject, spec = _checked_plan(plan, asset)
                except (ValueError, TypeError, KeyError):
                    continue
                if foundry.identifier(spec) in already:
                    continue
                chosen = (goal, question, reject, spec, "gemini_research_director")
                model_used += 1
                break
            if not chosen:
                for goal in targets:
                    spec = _local_plan(asset, goal, already)
                    if spec:
                        chosen = (goal, GOALS[goal][1], GOALS[goal][2],
                                  spec, "bounded_local_research_director")
                        break
            if not chosen:
                errors[asset] = "bounded_strategy_space_exhausted"
                # Keep a completed plan rather than silently emptying its
                # registered forward track when the bounded grammar runs out.
                if old:
                    selections[asset] = old_id
                    status[asset] = old.get("prospective_status", "no_untried_experiment")
                else:
                    status[asset] = "no_untried_experiment"
                continue
            goal, question, rejection, spec, origin = chosen
            key = foundry.identifier(spec)
            if key in already:
                raise ValueError("duplicate_strategy_id")
            # Freeze BEFORE research/strategy_foundry can evaluate history.
            frozen = {
                "id": key, "asset": asset, "goal": goal,
                "hypothesis": question, "rejection_rule": rejection,
                "method": "frozen_future_paper_strategy",
                "source": origin, "spec": spec,
                "closed_day_at_registration": last_t,
                "started_at": now.isoformat(),
                "prospective_status": "awaiting_prospective_data",
                "prospective_observed_days": 0,
                "historical_data_not_independent_validation": True,
                "real_orders": False, "robots_modified": False,
            }
            archive.append(frozen)
            if origin == "bounded_local_research_director":
                local_used += 1
            by_id[key] = frozen
            already.add(key)
            attempted.append(key)
            selections[asset] = key
            status[asset] = "experiment_registered"
        except (ValueError, KeyError, TypeError, OverflowError) as error:
            errors[asset] = str(error)[:70]
            if previous_active.get(asset) in by_id:
                selections[asset] = previous_active[asset]
                status[asset] = "paused_existing_experiment"
    archive = archive[-MAX_EXPERIMENTS:]
    ids = {item["id"] for item in archive}
    selections = {k:v for k,v in selections.items() if v in ids}
    state = {
        "schema": 1, "updated_at": now.isoformat(),
        "experiments": archive, "active_by_asset": selections,
        "attempted_ids": list(dict.fromkeys(attempted))[-MAX_ATTEMPTED:],
        "real_orders": False, "robot_changes": False,
    }
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "source": "falsifiable_research_director",
        "real_orders": False, "robot_changes": False,
        "active_by_asset": selections, "experiments": archive,
        "tracked": len(selections), "total_experiments": len(archive),
        "model_directed_this_cycle": model_used,
        "local_fallback_new_experiments": local_used,
        "status": status, "issues": errors, "observed_days": evidence_days,
        "selection_rule": "prospective_status_priority_else_falsifiable_untested_plan",
        "no_automatic_robot_promotion": True,
        "no_claim_of_autonomous_general_intelligence": True,
    }
    return report, state


def main():
    now = datetime.now(timezone.utc)
    report, state = build(now, read(CANDLES), read(SCIENCE), read(SCIENCE_STATE),
                          read(PROPOSALS), read(KNOWLEDGE), read(FORWARD), read(STATE))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Research director:", report["tracked"], "active,",
          report["model_directed_this_cycle"], "new model plans,",
          report["local_fallback_new_experiments"], "new fallback plans,",
          len(report["issues"]), "issues")


if __name__ == "__main__":
    main()
