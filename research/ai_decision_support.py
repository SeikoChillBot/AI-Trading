"""Deterministic, auditable evidence pack for the optional AI research reviewer.

All evidence is historical and read-only. This module never changes paper
portfolios, trading signals, brokerage settings, or order parameters.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math

ASSETS = ("BTCUSD", "ETHUSD", "SOLUSD")
MODEL = "kraken_daily_walkforward_v1"


def _number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if math.isfinite(result) else None


def summarize_challengers(report, now=None):
    """Require complete, fresh walk-forward evidence before exposing a candidate."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(report, dict) or report.get("model") != MODEL:
        return {"status": "missing_or_invalid", "assets": [], "eligible_for_automatic_promotion": False}
    try:
        created = datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))
        age = (now - created).total_seconds()
        if created.tzinfo is None or age < -300 or age > 72 * 3600:
            raise ValueError("stale timestamp")
    except (KeyError, TypeError, ValueError):
        return {"status": "missing_or_stale", "assets": [], "eligible_for_automatic_promotion": False}
    observations = []
    for asset in ASSETS:
        raw = report.get("instruments", {}).get(asset)
        if not isinstance(raw, dict):
            continue
        folds = raw.get("folds")
        if not isinstance(folds, list) or not 2 <= len(folds) <= 20 or raw.get("fold_count") != len(folds):
            continue
        values = []
        for fold in folds:
            if not isinstance(fold, dict):
                values = []
                break
            keys = ("oos_return_pct", "hold_return_pct", "cost_x2_return_pct",
                    "observed_drawdown_pct", "completed_trades", "excess_vs_hold_points")
            nums = [_number(fold.get(k)) for k in keys]
            if any(v is None for v in nums) or nums[3] < 0 or nums[4] < 0:
                values = []
                break
            values.append(dict(zip(keys, nums)))
        if not values:
            continue
        avg = lambda k: round(sum(v[k] for v in values) / len(values), 4)
        wins = sum(v["excess_vs_hold_points"] > 0 for v in values)
        positive = sum(v["oos_return_pct"] > 0 for v in values)
        stress_positive = sum(v["cost_x2_return_pct"] > 0 for v in values)
        trades = int(sum(v["completed_trades"] for v in values))
        worst_dd = round(max(v["observed_drawdown_pct"] for v in values), 4)
        params = raw.get("candidate_parameters", {})
        if not isinstance(params, dict) or params.get("window") not in (10, 20, 40) or params.get("buffer") not in (.005, .01, .02):
            continue
        checks = {
            "six_or_more_oos_folds": len(values) >= 6,
            "twenty_or_more_closed_trades": trades >= 20,
            "positive_average_net_return": avg("oos_return_pct") > 0,
            "beats_hold_in_most_folds": wins >= math.ceil(len(values) * 0.625),
            "positive_average_with_double_costs": avg("cost_x2_return_pct") > 0,
            "drawdown_below_20_pct": worst_dd < 20,
        }
        observations.append({
            "asset": asset, "folds": len(values),
            "positive_oos_folds": positive, "beats_hold_folds": wins,
            "positive_double_cost_folds": stress_positive,
            "closed_trades": trades,
            "avg_net_return_pct": avg("oos_return_pct"),
            "avg_excess_vs_hold_points": avg("excess_vs_hold_points"),
            "avg_net_return_double_cost_pct": avg("cost_x2_return_pct"),
            "worst_drawdown_pct": worst_dd,
            "latest_research_parameters": {"window": params["window"], "buffer": params["buffer"]},
            "research_checks": checks,
            "status": "requires_independent_forward_validation" if all(checks.values())
                      else "fails_one_or_more_research_checks",
            "automatic_promotion": False,
        })
    return {"status": "historical_evidence_available" if observations else "no_valid_evidence",
            "source": "Kraken daily OHLC, modeled execution costs; past selection bias possible",
            "assets": observations,
            "eligible_for_automatic_promotion": False,
            "risk_note": "Repeated research on the same holdouts can overfit. Further untouched data and prospective validation are required."}


def safe_context(research, historical):
    """Model input is bounded, without credentials or raw orders/wallet addresses."""
    labs = {}
    for name in ("crypto", "multi"):
        source = research.get("labs", {}).get(name, {})
        labs[name] = {
            "count": source.get("count"),
            "elapsed_days": source.get("elapsed_days"),
            "eligible_for_review": source.get("eligible"),
            "fees_paid_usd": source.get("fees_paid_usd"),
            "issues": source.get("issues", [])[:4],
        }
    hypotheses = []
    for item in research.get("hypotheses", [])[:6]:
        if isinstance(item, dict):
            hypotheses.append({key: item.get(key) for key in ("id", "domain", "title", "experiment", "state")})
    raw_pulse = research.get("market_pulse", {})
    observed = raw_pulse.get("assets", {}) if isinstance(raw_pulse, dict) else {}
    pulse = {
        "generated_at": raw_pulse.get("generated_at") if isinstance(raw_pulse, dict) else None,
        "assets": {name: {
            field: observed.get(name, {}).get(field) for field in (
                "last_closed_day_utc", "change_1d_pct", "change_7d_pct",
                "change_30d_pct", "realized_volatility_30d_annualized_pct"
            )} for name in ASSETS if isinstance(observed.get(name), dict)},
        "macro": {k: (raw_pulse.get("macro", {}).get(k) if isinstance(raw_pulse, dict) else None)
                  for k in ("fear_greed_index", "tvl_ethereum_usd", "tvl_solana_usd",
                            "stablecoin_supply_usd_estimate")},
        "large_transfer_sample": {
            k: (raw_pulse.get("large_transfers", {}).get(k) if isinstance(raw_pulse, dict) else None)
            for k in ("state", "coverage", "sampled_records", "large_transfers_observed",
                      "new_in_sample", "largest_nominal_usd")},
    }
    raw_hourly = research.get("hourly_research", {})
    raw_hourly = raw_hourly if isinstance(raw_hourly,dict) else {}
    hourly_assets = raw_hourly.get("assets", {})
    hourly_assets = hourly_assets if isinstance(hourly_assets,dict) else {}
    hourly = {
        "generated_at":raw_hourly.get("generated_at"),
        "status":raw_hourly.get("status"),
        "assets":{asset:{
            "historical_oos_avg_net_pct":info.get("historical_study",{}).get("avg_net_return_pct"),
            "oos_excess_vs_hold_points":info.get("historical_study",{}).get("avg_excess_vs_hold"),
            "worst_oos_drawdown_pct":info.get("historical_study",{}).get("max_drawdown_pct"),
            "forward_paper_observations":info.get("paper_forward",{}).get("observations"),
            "forward_paper_net_pct":info.get("paper_forward",{}).get("net_return_pct"),
        } for asset,info in hourly_assets.items() if asset in ASSETS and isinstance(info,dict)},
    }
    bot_reviews = []
    for lab in ("crypto", "multi"):
        for robot in research.get("labs", {}).get(lab, {}).get("strategies", []):
            if isinstance(robot, dict):
                bot_reviews.append({
                    "id": robot.get("strategy"), "lab": lab,
                    "asset": robot.get("asset"),
                    "net_return_pct": robot.get("net_return_pct"),
                    "drawdown_pct": robot.get("drawdown_pct"),
                    "closed_roundtrips": robot.get("completed_roundtrips"),
                    "observations": robot.get("observations"),
                    "ready_for_review": robot.get("ready_for_review"),
                })
    news = research.get("news_observations", {})
    highlights = []
    if isinstance(news, dict) and news.get("status") in ("available", "partial"):
        for article in news.get("articles", [])[:5]:
            if isinstance(article, dict) and article.get("source") in ("Fed", "BCE", "CoinDesk"):
                highlights.append({k:article.get(k) for k in
                                   ("source","category","title","published_at")})
    return {"hourly_oos_and_forward_paper":hourly,
            "news_headlines_unverified": highlights, "robot_reviews": bot_reviews[:36], "market_pulse": pulse, "research_date_utc": research.get("research_date_utc"),
            "qualification": research.get("qualification", {}),
            "labs": labs, "hypotheses": hypotheses,
            "historical": historical,
            "strategy_research_memory": research.get("strategy_research_memory", {}),
            "market_knowledge_memory": research.get("market_knowledge_memory", {}),
            "independent_optimizer_memory": research.get("independent_optimizer_memory", {}),
            "mutation_memory": research.get("mutation_memory", {}),
            "independent_hypothesis_memory": research.get("independent_hypothesis_memory", {}),
            "paper_league_memory": research.get("paper_league_memory", {}),
            "budget_per_strategy_usd": 20,
            "allow_live_trading": False, "allow_live_strategy_changes": False}


def baseline_ideas(historical):
    """Readable no-model fallback. These are research tasks, NOT validated gains."""
    outcome = []
    for item in historical.get("assets", []):
        blocks = [k for k, ok in item["research_checks"].items() if not ok]
        outcome.append({
            "asset": item["asset"],
            "title": "Contrôler la robustesse historique de " + item["asset"],
            "hypothesis": "Les paramètres actuels peuvent être sensibles aux frais et au régime de marché.",
            "experiment": "Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils.",
            "rejection_rule": "Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.",
            "evidence_state": "non_validated",
            "blocking_checks": blocks,
        })
    return outcome


def validate_model_ideas(value, assets):
    """Reject out-of-scope model suggestions before writing site-facing JSON."""
    if not isinstance(value, dict) or not isinstance(value.get("summary"), str):
        raise ValueError("Invalid AI result")
    ideas = value.get("experiments")
    if not isinstance(ideas, list) or len(ideas) > 3:
        raise ValueError("Invalid number of experiments")
    clean = []
    for item in ideas:
        if not isinstance(item, dict) or item.get("asset") not in assets:
            raise ValueError("Unrecognized research asset")
        keys = ("title", "hypothesis", "experiment", "rejection_rule")
        if any(not isinstance(item.get(k), str) or not 8 <= len(item[k].strip()) <= 700 for k in keys):
            raise ValueError("Missing or oversized experiment field")
        clean.append({"asset": item["asset"], **{k: item[k].strip() for k in keys},
                      "evidence_state": "ai_hypothesis_not_tested",
                      "blocking_checks": next((x["blocking_checks"] for x in baseline_ideas({"assets": assets.values()}) if x["asset"] == item["asset"]), [])})
    from research.robot_tuning import TUNABLE_CRYPTO, TUNABLE_MULTI
    proposals = value.get("bot_adjustments", [])
    if not isinstance(proposals, list) or len(proposals) > 3:
        raise ValueError("Invalid number of robot suggestions")
    bot_adjustments = []
    seen = set()
    for candidate in proposals:
        if not isinstance(candidate, dict):
            raise ValueError("Invalid robot tuning payload")
        name = candidate.get("strategy")
        profile = candidate.get("profile")
        reason = candidate.get("reason")
        if (name not in TUNABLE_CRYPTO | TUNABLE_MULTI
                or name in seen or profile not in ("conservative", "responsive")
                or not isinstance(reason, str) or not 12 <= len(reason.strip()) <= 450):
            raise ValueError("Robot suggestion outside reviewed safe parameter grid")
        seen.add(name)
        bot_adjustments.append({
            "strategy": name, "entry_scale": 1.2 if profile == "conservative" else 0.8,
            "reason": reason.strip(), "evidence_state": "gemini_hypothesis_unverified",
        })
    scenario_items = value.get("scenario_proposals", [])
    if not isinstance(scenario_items, list) or len(scenario_items) > 2:
        raise ValueError("Invalid number of sandbox placement hypotheses")
    trials = []
    seen_trials = set()
    for item in scenario_items:
        if not isinstance(item, dict):
            raise ValueError("Invalid sandbox hypothesis")
        asset, trigger, horizon = (item.get("asset"), item.get("trigger"),
                                   item.get("horizon_days"))
        rationale = item.get("rationale")
        if (asset not in ("BTCUSD","ETHUSD","SOLUSD")
                or trigger not in ("market_uptrend","market_selloff","sampled_large_transfer")
                or type(horizon) is not int or horizon not in (1,3,7)
                or not isinstance(rationale,str)
                or not 12 <= len(rationale.strip()) <= 350):
            raise ValueError("Unapproved trial request")
        key = (asset, trigger, horizon)
        if key in seen_trials:
            continue
        seen_trials.add(key)
        trials.append({"asset":asset,"trigger":trigger,"horizon_days":horizon,
                       "rationale":rationale.strip(),"status":"hypothesis_not_executed"})
    note_items = value.get("desk_notes", [])
    if not isinstance(note_items, list) or len(note_items) > 3:
        raise ValueError("Invalid note count")
    notes = []
    for item in note_items:
        if (not isinstance(item,dict) or item.get("category") not in
            ("marche","strategie","baleines","risque")
            or not isinstance(item.get("text"),str)
            or not 12 <= len(item["text"].strip()) <= 420):
            raise ValueError("Invalid research note")
        notes.append({"category":item["category"],"text":item["text"].strip(),
                      "status":"non_verified_analyst_interpretation"})
    # Bounded strategy grammar; Gemini supplies parameters, never runnable code.
    # A missing field is accepted for older cached Gemini responses.
    from research.strategy_foundry import normalise, identifier
    designs = value.get("strategy_designs", [])
    if not isinstance(designs, list) or len(designs) > 2:
        raise ValueError("Invalid number of strategy designs")
    valid_designs = []
    seen_designs = set()
    for raw in designs:
        try:
            spec = normalise(raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Strategy outside approved research grammar") from error
        key = identifier(spec)
        if key in seen_designs:
            continue
        seen_designs.add(key)
        valid_designs.append(spec)
    return {"summary": value["summary"].strip()[:1000], "experiments": clean,
            "bot_adjustments": bot_adjustments,
            "scenario_proposals": trials, "desk_notes": notes,
            "strategy_designs": valid_designs}
