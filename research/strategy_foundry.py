"""Persistent, bounded AIT strategy foundry. Research only, NEVER robot execution.

Gemini may propose strategies through a strict finite grammar. Python owns all
logic, historical replay, provenance, data checks and persistent results.
Historical outcomes are exploratory: the model has already seen related data.
Never promote to a 36-robot account from this file.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = ROOT / "reports/ai_research_proposals.json"
CANDLES = ROOT / "reports/challenger_candles.json"
MEMORY = ROOT / "state/strategy_knowledge_base.json"
REPORT = ROOT / "reports/strategy_foundry.json"
MARKDOWN = ROOT / "reports/strategy_foundry.md"
OPTIMIZER = ROOT / "reports/autonomous_optimizer.json"
EVOLUTION = ROOT / "reports/strategy_evolution.json"
ASSETS = ("BTCUSD", "ETHUSD", "SOLUSD")
LOGICS = ("trend_following", "mean_reversion", "breakout",
          "ema_trend", "rsi_reversal", "volatility_gate", "dual_confirmation")
WINDOWS = (10, 20, 40)
THRESHOLDS = (0.5, 1, 2)
MAX_HOLD = (1, 3, 7)
# Optional independent signal gates make auditable multi-indicator combinations.
CONFIRMATIONS = ("rsi_oversold", "rsi_strength", "ema_uptrend",
                 "quiet_volatility", "active_volatility", "positive_momentum")
MAX_CONFIRMATIONS = 2
CAPITAL = 20.0
COST = .009  # Hypothetical fee, spread and slippage PER SIDE.
MAX_IDEAS = 80
MAX_HISTORY = 8
TEST_DAYS = 60
TEST_FOLDS = 6


def read(path):
    try:
        x = json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def normalise(raw):
    """Accept only declarative, finite, auditable strategy parameters."""
    if not isinstance(raw, dict):
        raise ValueError("not_an_object")
    asset, logic = raw.get("asset"), raw.get("logic")
    window, horizon = raw.get("lookback_days"), raw.get("max_hold_days")
    threshold = raw.get("threshold_pct")
    if (asset not in ASSETS or logic not in LOGICS
            or type(window) is not int or window not in WINDOWS
            or type(horizon) is not int or horizon not in MAX_HOLD
            or type(threshold) not in (int, float)
            or not math.isfinite(threshold)
            or threshold not in (0.5, 1, 2)):
        raise ValueError("not_in_approved_strategy_grammar")
    rationale = raw.get("rationale", "")
    if not isinstance(rationale, str) or not 12 <= len(rationale.strip()) <= 350:
        raise ValueError("missing_bounded_rationale")
    gates = raw.get("confirmations", [])
    if (not isinstance(gates, list) or len(gates) > MAX_CONFIRMATIONS
            or any(type(gate) is not str or gate not in CONFIRMATIONS for gate in gates)
            or len(set(gates)) != len(gates)
            or {"quiet_volatility", "active_volatility"} <= set(gates)
            or {"rsi_oversold", "rsi_strength"} <= set(gates)):
        raise ValueError("invalid_signal_confirmations")
    spec = {
        "asset": asset, "logic": logic, "lookback_days": window,
        "threshold_pct": float(threshold), "max_hold_days": horizon,
        "rationale": rationale.strip(),
    }
    if gates:
        spec["confirmations"] = sorted(gates)
    return spec


def identifier(spec):
    exact = {k: spec[k] for k in
             ("asset", "logic", "lookback_days", "threshold_pct", "max_hold_days")}
    if spec.get("confirmations"):
        gates = spec["confirmations"]
        if (not isinstance(gates, list) or len(gates) > MAX_CONFIRMATIONS
                or any(g not in CONFIRMATIONS for g in gates)
                or len(set(gates)) != len(gates)):
            raise ValueError("invalid_signal_confirmations")
        exact["confirmations"] = sorted(gates)
    return hashlib.sha256(json.dumps(exact, sort_keys=True).encode()).hexdigest()[:18]


def validate_bars(bars, now):
    if not isinstance(bars, list) or len(bars) < 400 or len(bars) > 1500:
        raise ValueError("missing_complete_closed_daily_history")
    previous = None
    for bar in bars:
        if not isinstance(bar, dict) or type(bar.get("t")) is not int:
            raise ValueError("invalid_candle")
        stamp = bar["t"]
        if stamp <= 1e8 or stamp + 86400 > now.timestamp():
            raise ValueError("not_a_closed_daily_candle")
        for key in ("open", "close"):
            try:
                price = float(bar[key])
            except (TypeError, ValueError, KeyError):
                raise ValueError("invalid_price") from None
            if not math.isfinite(price) or price <= 0:
                raise ValueError("invalid_price")
        if previous is not None and stamp - previous != 86400:
            raise ValueError("missing_or_duplicate_daily_candle")
        previous = stamp
    if now.timestamp() - bars[-1]["t"] > 5 * 86400:
        raise ValueError("stale_daily_data")


def _ema(values, period):
    """Finite EMA on CLOSED observations only, without external libraries."""
    factor = 2 / (period + 1)
    value = float(values[0])
    for close in values[1:]:
        value += factor * (float(close) - value)
    return value


def _rsi(closes, i, window):
    """RSI available when deciding at next open, no current candle."""
    differences = [closes[k] - closes[k - 1] for k in range(i - window, i)]
    gains = sum(max(0., d) for d in differences) / window
    losses = sum(max(0., -d) for d in differences) / window
    if gains == 0 and losses == 0:
        return 50.
    if losses == 0:
        return 100.
    return 100. - 100. / (1. + gains / losses)


def _base_signal(closes, i, spec, holding, age):
    """At open(i), inspect only closes through i-1. Never inspect close(i)."""
    w = spec["lookback_days"]
    if i < w + 2 or i > len(closes):
        raise ValueError("insufficient_prior_closed_candles")
    before = closes[i - w:i]
    last = before[-1]
    average = sum(before) / w
    band = spec["threshold_pct"] / 100.
    logic = spec["logic"]
    if logic in ("ema_trend", "dual_confirmation", "rsi_reversal", "volatility_gate"):
        # Only past closes; indicators must share the same temporal cutoff.
        ema_slow = _ema(before, w)
        ema_fast = _ema(before, max(3, w // 2))
        rsi = _rsi(closes, i, w)
        changes = [(closes[j] / closes[j - 1] - 1)
                   for j in range(i - w + 1, i)]
        mean_change = sum(changes) / len(changes)
        volatility = math.sqrt(sum((v - mean_change) ** 2
                                   for v in changes) / len(changes))
    if holding:
        if age >= spec["max_hold_days"]:
            return "SELL"
        if logic == "mean_reversion":
            return "SELL" if last >= average else "WAIT"
        if logic == "rsi_reversal":
            return "SELL" if rsi >= 50. + spec["threshold_pct"] * 4 else "WAIT"
        if logic == "ema_trend":
            return "SELL" if ema_fast < ema_slow or last < ema_slow else "WAIT"
        if logic == "dual_confirmation":
            return "SELL" if rsi < 45 or last < average else "WAIT"
        return "SELL" if last < average else "WAIT"
    if logic == "trend_following":
        return "BUY" if last > average * (1 + band) and last > closes[i - 2] else "WAIT"
    if logic == "mean_reversion":
        return "BUY" if last < average * (1 - band) else "WAIT"
    if logic == "breakout":
        prior_high = max(closes[i - w - 1:i - 1])
        return "BUY" if last > prior_high * (1 + band) else "WAIT"
    if logic == "ema_trend":
        return "BUY" if ema_fast > ema_slow * (1 + band) and last > closes[i - 2] else "WAIT"
    if logic == "rsi_reversal":
        return "BUY" if rsi < 30. + spec["threshold_pct"] * 5 and last < average else "WAIT"
    if logic == "volatility_gate":
        return "BUY" if (last > average * (1 + band)
                        and volatility < 0.015 + band) else "WAIT"
    if logic == "dual_confirmation":
        return "BUY" if (last > average * (1 + band)
                        and ema_fast > ema_slow
                        and 50 < rsi < 75) else "WAIT"
    raise ValueError("invalid_strategy_logic")



def _confirmation_passes(closes, i, spec):
    """Evaluate composition gates from COMPLETED candles before open(i)."""
    if not spec.get("confirmations"):
        return True
    w = spec["lookback_days"]
    prior = closes[i-w:i]
    returns = [prior[k] / prior[k-1] - 1 for k in range(1, len(prior))]
    avg = sum(returns) / len(returns)
    volatility = math.sqrt(sum((r - avg) ** 2 for r in returns) / len(returns))
    for gate in spec.get("confirmations", []):
        if gate == "rsi_oversold":
            passed = _rsi(closes, i, w) <= 40
        elif gate == "rsi_strength":
            passed = _rsi(closes, i, w) >= 55
        elif gate == "ema_uptrend":
            passed = _ema(prior, max(3, w//2)) > _ema(prior, w)
        elif gate == "quiet_volatility":
            passed = volatility < .025
        elif gate == "active_volatility":
            passed = volatility >= .025
        elif gate == "positive_momentum":
            passed = closes[i-1] > closes[i-3]
        else:
            raise ValueError("invalid_signal_confirmations")
        if not passed:
            return False
    return True


def signal(closes, i, spec, holding, age):
    """Composable, frozen and auditably point-in-time strategy decision."""
    action = _base_signal(closes, i, spec, holding, age)
    if action == "BUY" and not _confirmation_passes(closes, i, spec):
        return "WAIT"
    return action

def replay(bars, spec, start, end, fee=COST):
    """Independent forward chronological fold with previous-close decisions.

    This is NOT an untouched out-of-sample test: candidate design can be
    influenced by previous model exposure to the same historical prices.
    """
    if not 42 <= start < end <= len(bars) or not 0 <= fee <= .05:
        raise ValueError("invalid_replay_bounds")
    closes = [float(x["close"]) for x in bars]
    cash, units, age = CAPITAL, 0., 0
    peak, worst = CAPITAL, 0.
    completed, orders = 0, 0
    for i in range(start, end):
        action = signal(closes, i, spec, units > 0, age)
        opening = float(bars[i]["open"])
        if action == "BUY" and not units:
            units = cash / (opening * (1 + fee))
            cash = 0.
            age = 0
            orders += 1
        elif action == "SELL" and units:
            cash = units * opening * (1 - fee)
            units = 0.
            age = 0
            completed += 1
            orders += 1
        if units:
            age += 1
        equity = cash + units * closes[i] * (1 - fee)
        if not math.isfinite(equity) or equity < 0:
            raise ValueError("invalid_equity")
        peak = max(peak, equity)
        worst = max(worst, (peak - equity) / peak * 100)
    if units:
        cash = units * closes[end - 1] * (1 - fee)
        completed += 1
        orders += 1
    return {
        "net_pct": round((cash / CAPITAL - 1) * 100, 5),
        "drawdown_pct": round(worst, 5),
        "closed_trades": completed, "orders": orders,
    }


def benchmark(bars, start, end, fee=COST):
    acquired = CAPITAL / (float(bars[start]["open"]) * (1 + fee))
    exit_equity = acquired * float(bars[end - 1]["close"]) * (1 - fee)
    return round((exit_equity / CAPITAL - 1) * 100, 5)


def evaluate(bars, spec, now):
    validate_bars(bars, now)
    # Six historical chronological 60-day segments; specifications are frozen.
    # Do not report them as blind OOS because Gemini has seen historical summaries.
    start = len(bars) - TEST_DAYS * TEST_FOLDS
    folds = []
    for f in range(TEST_FOLDS):
        a, b = start + f * TEST_DAYS, start + (f + 1) * TEST_DAYS
        normal = replay(bars, spec, a, b)
        stress = replay(bars, spec, a, b, fee=COST * 2)
        witness = benchmark(bars, a, b)
        folds.append({
            "first_day": bars[a]["t"], "last_day": bars[b - 1]["t"],
            **normal, "double_cost_net_pct": stress["net_pct"],
            "hold_net_pct": witness,
            "excess_vs_hold_points": round(normal["net_pct"] - witness, 5),
        })
    average = lambda key: round(sum(v[key] for v in folds) / len(folds), 4)
    trades = sum(v["closed_trades"] for v in folds)
    wins = sum(v["excess_vs_hold_points"] > 0 for v in folds)
    checks = {
        "enough_closed_trades": trades >= 20,
        "positive_average_net": average("net_pct") > 0,
        "positive_with_double_costs": average("double_cost_net_pct") > 0,
        "beats_hold_in_most_folds": wins >= 4,
        "drawdown_under_20_pct": max(v["drawdown_pct"] for v in folds) < 20,
    }
    return {
        "evidence_kind": "exploratory_historical_replay_not_blind_oos",
        "source": "Kraken closed daily OHLC snapshot; modeled fills at next open",
        "model_has_seen_related_history": True,
        "asset": spec["asset"], "folds": folds,
        "average_net_pct": average("net_pct"),
        "average_excess_vs_hold_points": average("excess_vs_hold_points"),
        "average_double_cost_net_pct": average("double_cost_net_pct"),
        "max_drawdown_pct": max(v["drawdown_pct"] for v in folds),
        "closed_trades": trades, "folds_beating_hold": wins,
        "checks": checks, "all_historical_checks_pass": all(checks.values()),
        "qualified_for_live_trading": False, "qualified_for_robot_promotion": False,
        "next_step": "Prospective unseen paper data and execution-quality audit required",
    }


def seed_specs():
    """Non-LLM reference experiments keep research alive when Gemini fails."""
    return [
        {"asset": asset, "logic": logic, "lookback_days": 20,
         "threshold_pct": 1, "max_hold_days": 3,
         "rationale": "Référence quantitative figée pour comparer cette logique au témoin Hold."}
        for asset, logic in zip(ASSETS, LOGICS)
    ]


def model_memory(ledger):
    """Limited, sanitized ledger summary available to Gemini in the next cycle."""
    ideas = ledger.get("ideas", []) if isinstance(ledger, dict) else []
    if not isinstance(ideas, list):
        return {"prior_ideas": []}
    recent = []
    for idea in ideas[-12:]:
        if not isinstance(idea, dict):
            continue
        spec = idea.get("spec", {})
        result = idea.get("latest_result", {})
        if not isinstance(spec, dict) or not isinstance(result, dict):
            continue
        if spec.get("logic") not in LOGICS or spec.get("asset") not in ASSETS:
            continue
        recent.append({
            "id": str(idea.get("id", ""))[:18],
            "asset": spec.get("asset"), "logic": spec.get("logic"),
            "lookback_days": spec.get("lookback_days"),
            "threshold_pct": spec.get("threshold_pct"),
            "max_hold_days": spec.get("max_hold_days"),
            "source": idea.get("source"),
            "average_net_pct": result.get("average_net_pct"),
            "beats_hold_folds": result.get("folds_beating_hold"),
            "trades": result.get("closed_trades"),
            "failed_checks": [key for key, value in result.get("checks", {}).items()
                              if value is False][:5],
            "evaluation_type": result.get("evidence_kind"),
        })
    return {"prior_ideas": recent[-8:], "memory_scope": "historical_hypotheses_not_proven",
            "instruction": "Learn from failures; do not retest the same parameters just to claim success."}


def build(now, proposals, candles, previous, optimizer=None, evolution=None):
    ideas = [dict(x) for x in previous.get("ideas", [])
             if isinstance(x, dict) and isinstance(x.get("spec"), dict)][-MAX_IDEAS:]
    existing = {i.get("id"): i for i in ideas}
    events = []
    # The origin of model ideas must be proven. Never execute plain language.
    generated = (proposals.get("strategy_designs", [])
                 if proposals.get("source") == "gemini_generate_content"
                 and proposals.get("state") == "model_reflection_completed" else [])
    if not isinstance(generated, list):
        generated = []
    submissions = [(x, "gemini_structured_hypothesis") for x in generated[:2]]
    # Adaptive, deterministic search also contributes paper-only specifications.
    # Historical optimization provenance must not be relabelled as Gemini.
    if (isinstance(optimizer, dict)
            and optimizer.get("schema") == 1
            and optimizer.get("source") == "autonomous_grid_search"
            and optimizer.get("real_orders") is False
            and optimizer.get("robot_changes") is False):
        best = optimizer.get("latest_by_asset", {})
        pool = optimizer.get("candidates", [])
        pool = pool if isinstance(pool, list) else []
        best = best if isinstance(best, dict) else {}
        for asset in ASSETS:
            identifier_value = best.get(asset)
            for item in pool[-MAX_IDEAS:]:
                if (isinstance(item, dict) and item.get("id") == identifier_value
                        and item.get("source") == "autonomous_grid_search"
                        and item.get("historical_candidate_only") is True
                        and item.get("eligible_for_live_trading") is False):
                    raw = item.get("spec")
                    try:
                        valid = normalise(raw)
                        if valid["asset"] == asset and identifier(valid) == identifier_value:
                            submissions.append((valid, "autonomous_grid_search"))
                    except (ValueError, TypeError, KeyError):
                        pass
                    break
    # Only proven declarative, fixed and research-only mutations enter the archive.
    if (isinstance(evolution, dict) and evolution.get("schema") == 1
            and evolution.get("source") == "bounded_evolution"
            and evolution.get("real_orders") is False
            and evolution.get("robot_changes") is False):
        pool = evolution.get("candidates", [])
        chosen = evolution.get("selected_by_asset", {})
        if isinstance(pool, list) and isinstance(chosen, dict):
            for asset in ASSETS:
                wanted = chosen.get(asset)
                for item in pool[-MAX_IDEAS:]:
                    if (not isinstance(item, dict) or item.get("id") != wanted
                            or item.get("source") != "bounded_evolution"
                            or item.get("historical_candidate_only") is not True
                            or item.get("eligible_for_live_trading") is not False):
                        continue
                    try:
                        spec = normalise(item["spec"])
                        if spec["asset"] == asset and identifier(spec) == wanted:
                            submissions.append((spec, "bounded_evolution"))
                    except (ValueError, TypeError, KeyError):
                        pass
                    break
    submissions += [(x, "deterministic_reference") for x in seed_specs()]
    for raw, origin in submissions:
        try:
            spec = normalise(raw)
        except (ValueError, TypeError):
            events.append({"status": "rejected_invalid_strategy_spec", "source": origin})
            continue
        idea_id = identifier(spec)
        if idea_id not in existing:
            item = {
                "id": idea_id, "source": origin, "spec": spec,
                "created_at": now.isoformat(), "review_count": 0,
                "history": [], "status": "awaiting_data",
            }
            ideas.append(item)
            existing[idea_id] = item
            events.append({"id": idea_id, "status": "hypothesis_archived", "source": origin})
    ideas = ideas[-MAX_IDEAS:]
    for idea in ideas:
        spec = idea["spec"]
        # Historical records survive data outages without inventing new results.
        bars = candles.get(spec.get("asset")) if isinstance(candles, dict) else None
        try:
            evidence = evaluate(bars, spec, now)
            digest = hashlib.sha256(json.dumps(
                bars, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if idea.get("latest_data_sha256") == digest:
                continue
            idea["latest_data_sha256"] = digest
            idea["latest_result"] = evidence
            idea["last_reviewed_at"] = now.isoformat()
            idea["review_count"] = int(idea.get("review_count", 0)) + 1
            idea["status"] = "historical_exploration_only"
            idea["history"] = (idea.get("history", []) + [{
                "reviewed_at": now.isoformat(), "data_sha256": digest,
                "average_net_pct": evidence["average_net_pct"],
                "folds_beating_hold": evidence["folds_beating_hold"],
                "historical_checks_pass": evidence["all_historical_checks_pass"],
            }])[-MAX_HISTORY:]
            events.append({"id": idea["id"], "status": "exploratory_replay_completed"})
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            events.append({"id": idea.get("id"),
                           "status": "no_valid_replay", "reason": str(error)[:60]})
    ledger = {
        "schema": 1, "updated_at": now.isoformat(), "ideas": ideas,
        "never_run_model_code": True, "real_orders": False,
        "promotions_enabled": False, "scope": "research_only",
    }
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "total_hypotheses": len(ideas),
        "gemini_hypotheses": sum(x.get("source") == "gemini_structured_hypothesis" for x in ideas),
        "auto_optimized_hypotheses": sum(x.get("source") == "autonomous_grid_search" for x in ideas),
        "evolved_hypotheses": sum(x.get("source") == "bounded_evolution" for x in ideas),
        "tested_historically": sum(isinstance(x.get("latest_result"), dict) for x in ideas),
        "events": events, "recent_ideas": [{
            "id": x.get("id"), "source": x.get("source"),
            "spec": x.get("spec"), "status": x.get("status"),
            "result": {k: v for k, v in x.get("latest_result", {}).items()
                       if k != "folds"}
        } for x in ideas[-12:]],
        "no_live_trades": True, "no_robot_modification": True,
        "warning": "Exploratory tests on reused history are not independent evidence of profitability.",
    }
    return ledger, report


def main():
    now = datetime.now(timezone.utc)
    ledger, report = build(now, read(PROPOSALS), read(CANDLES), read(MEMORY), read(OPTIMIZER), read(EVOLUTION))
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# AIT — Atelier autonome de stratégies",
        "",
        "Bilan du " + now.isoformat() + ". Simulation et recherche seulement.",
        "",
        "Hypothèses conservées : " + str(report["total_hypotheses"])
        + " ; proposées par Gemini : " + str(report["gemini_hypotheses"])
        + " ; rejouées sur l'histoire : " + str(report["tested_historically"]) + ".",
        "",
        "Les stratégies sont définies par un langage de règles borné ; aucun code IA n'est exécuté.",
        "Les replay historiques ne sont PAS une preuve hors échantillon vierge : Gemini a pu voir les mêmes cours.",
        "Les 36 robots et leurs témoins ne sont jamais modifiés par cet atelier.",
    ]
    for idea in report["recent_ideas"]:
        spec = idea["spec"]
        result = idea["result"]
        rows.append("")
        rows.append("- " + str(idea["id"]) + " " + spec["asset"] + " / "
                    + spec["logic"] + " / " + str(spec["lookback_days"]) + " j / "
                    + str(spec["threshold_pct"]) + "% : "
                    + ("moyenne historique " + str(result["average_net_pct"]) + "%, "
                       + str(result["folds_beating_hold"]) + "/6 fenêtres au-dessus de Hold"
                       if "average_net_pct" in result else "données indisponibles"))
    MARKDOWN.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("Strategy foundry:", report["total_hypotheses"],
          "ideas,", report["tested_historically"], "historical replays")


if __name__ == "__main__":
    main()
