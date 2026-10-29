"""Self-directed paper-only hypothesis architect for AIT.

Recombine frozen rules and two independent indicators into new candidates.
Select on earlier development folds only; read the reused challenge later.
This is auditable experiment design, not an LLM, machine learning weights, or
proof of out-of-sample performance.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from itertools import combinations, permutations
from pathlib import Path

from research import strategy_foundry as foundry
from research import autonomous_optimizer as optimizer

ROOT = Path(__file__).resolve().parents[1]
CANDLES = ROOT / "reports/challenger_candles.json"
KNOWLEDGE = ROOT / "state/strategy_knowledge_base.json"
EVOLUTION = ROOT / "reports/strategy_evolution.json"
STATE = ROOT / "state/strategy_architect.json"
REPORT = ROOT / "reports/strategy_architect.json"
ARCHIVE_LIMIT = 90
NEW_PER_ASSET = 2
SEARCH_EVERY_CLOSED_DAYS = 7
GATE_PAIRS = (
    ("rsi_strength", "ema_uptrend"),
    ("quiet_volatility", "positive_momentum"),
    ("rsi_oversold", "quiet_volatility"),
    ("active_volatility", "rsi_strength"),
    ("positive_momentum", "ema_uptrend"),
    ("rsi_strength", "quiet_volatility"),
)


def read(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def regime(bars):
    """Descriptive only: the current CLOSED price regime is not fit evidence."""
    closes = [float(b["close"]) for b in bars[-45:]]
    if len(closes) < 40:
        raise ValueError("insufficient_regime_history")
    changes = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    tail = changes[-30:]
    avg = sum(tail) / len(tail)
    deviation = math.sqrt(sum((r - avg) ** 2 for r in tail) / len(tail))
    change = 100 * (closes[-1] / closes[-31] - 1)
    trend = ("uptrend" if change >= 4 else "downtrend" if change <= -4
             else "sideways")
    vol = "high_volatility" if deviation >= .025 else "low_volatility"
    return {"last_closed_day": bars[-1]["t"], "trend": trend,
            "volatility_regime": vol,
            "trailing_30d_price_change_pct": round(change, 3),
            "trailing_daily_volatility_pct": round(100 * deviation, 3),
            "causal_predictive_claim": False}


def candidate_specs(asset, parents, tried):
    """Crossover of validated parents; at most 6 gate pairs for each pair.

    Explicit finite grammar. Never execute text/code provided by Gemini.
    """
    pool = parents[:5]
    for first, second in permutations(pool, 2):
        a, b = first["spec"], second["spec"]
        # Crossover: signal family from parent A, window and horizon from B.
        # Add two separate confirmations for novel, falsifiable combinations.
        for gates in GATE_PAIRS:
            raw = {
                "asset": asset, "logic": a["logic"],
                "lookback_days": b["lookback_days"],
                "threshold_pct": a["threshold_pct"],
                "max_hold_days": b["max_hold_days"],
                "confirmations": list(gates),
                "rationale": (
                    "Croisement expérimental de deux hypothèses antérieures avec "
                    "deux confirmations distinctes; les profits restent inconnus."
                ),
            }
            try:
                spec = foundry.normalise(raw)
                key = foundry.identifier(spec)
            except (ValueError, TypeError, KeyError):
                continue
            if key not in tried:
                yield key, spec, first["id"], second["id"]


def verified_parents(knowledge, asset):
    results = []
    rows = knowledge.get("ideas", []) if isinstance(knowledge, dict) else []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or not isinstance(row.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(row["spec"])
            if spec["asset"] != asset or row.get("id") != foundry.identifier(spec):
                continue
            if not isinstance(row.get("latest_result"), dict):
                continue
            results.append({"id": row["id"], "spec": spec,
                            "origin": str(row.get("source", "unknown"))[:50]})
        except (ValueError, TypeError, KeyError):
            continue
    # Prefer independent starting hypotheses, then evolved ones.
    return sorted(results, key=lambda x: (
        x["origin"] not in ("deterministic_reference", "autonomous_grid_search"),
        x["id"],
    ))[:10]


def build(now, candles, knowledge, previous):
    prior = previous if isinstance(previous, dict) else {}
    recent = prior.get("candidates", [])
    remembered = {}
    for row in recent[-ARCHIVE_LIMIT:] if isinstance(recent, list) else []:
        if not isinstance(row, dict) or not isinstance(row.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(row["spec"])
            if row.get("id") == foundry.identifier(spec):
                remembered[row["id"]] = row
        except (ValueError, TypeError, KeyError):
            continue
    tried = set(remembered)
    for row in knowledge.get("ideas", []) if isinstance(knowledge, dict) else []:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            tried.add(row["id"])
    last_search = dict(prior.get("last_search_closed_day", {})) if isinstance(
        prior.get("last_search_closed_day"), dict) else {}
    active = {}
    labels, findings, issues, new = {}, [], {}, []
    for asset in foundry.ASSETS:
        bars = candles.get(asset) if isinstance(candles, dict) else None
        try:
            foundry.validate_bars(bars, now)
            labels[asset] = regime(bars)
            last_t = bars[-1]["t"]
            previous_t = last_search.get(asset)
            if (type(previous_t) is int
                    and last_t - previous_t < SEARCH_EVERY_CLOSED_DAYS * 86400):
                ids = prior.get("selected_by_asset", {}).get(asset, [])
                if isinstance(ids, list):
                    active[asset] = [key for key in ids if key in remembered][:NEW_PER_ASSET]
                continue
            parents = verified_parents(knowledge, asset)
            if len(parents) < 2:
                raise ValueError("need_two_frozen_historical_parents")
            ranked = []
            for key, spec, ancestor_a, ancestor_b in candidate_specs(asset, parents, tried):
                score = optimizer.score_development(bars, spec)
                ranked.append((score["score"], key, spec, ancestor_a, ancestor_b, score))
            if not ranked:
                findings.append({"asset": asset, "status": "no_novel_recombinations"})
                last_search[asset] = last_t
                continue
            ranked.sort(key=lambda row: (-row[0], row[1]))
            # Keep two independent combinations whenever possible; do NOT
            # use later challenge folds to choose candidates.
            winners = []
            signatures = set()
            for candidate in ranked:
                signature = tuple(candidate[2]["confirmations"])
                if signature in signatures:
                    continue
                signatures.add(signature)
                winners.append(candidate)
                if len(winners) == NEW_PER_ASSET:
                    break
            active[asset] = []
            for _, key, spec, pa, pb, score in winners:
                if key not in remembered:
                    control = optimizer.challenge(bars, spec)
                    remembered[key] = {
                        "id": key, "source": "autonomous_crossover",
                        "asset": asset, "parent_ids": [pa, pb],
                        "hypothesis": "Le croisement et les confirmations peuvent filtrer des signaux; effet à mesurer.",
                        "rejection_rule": "Rejeter l'amélioration si les nouvelles performances fictives après frais ne surpassent pas le témoin.",
                        "spec": spec, "selection_metrics": score,
                        "historical_challenge": control,
                        "registered_on_closed_day": last_t,
                        "historical_candidate_only": True,
                        "eligible_for_live_trading": False,
                        "created_at": now.isoformat(),
                    }
                    new.append(key)
                active[asset].append(key)
            last_search[asset] = last_t
            findings.append({"asset": asset, "status": "experimental_crossover_created",
                             "explored": len(ranked),
                             "selected": list(active[asset]),
                             "historical_only": True})
        except (TypeError, ValueError, KeyError, OverflowError) as error:
            issues[asset] = str(error)[:80]
            prior_ids = prior.get("selected_by_asset", {}).get(asset, [])
            if isinstance(prior_ids, list):
                active[asset] = [k for k in prior_ids if k in remembered][:NEW_PER_ASSET]
    archive = list(remembered.values())[-ARCHIVE_LIMIT:]
    allowed = {r["id"] for r in archive}
    active = {asset: [key for key in keys if key in allowed]
              for asset, keys in active.items()}
    state = {"schema": 1, "updated_at": now.isoformat(),
             "candidates": archive, "selected_by_asset": active,
             "last_search_closed_day": last_search,
             "real_orders": False, "robot_changes": False}
    report = {"schema": 1, "generated_at": now.isoformat(),
              "source": "autonomous_crossover", "real_orders": False,
              "robot_changes": False, "archived_candidates": len(archive),
              "new_candidate_ids": new, "candidates": archive,
              "selected_by_asset": active, "observed_price_regimes": labels,
              "experiments": findings, "issues": issues,
              "reused_history_not_independent_evidence": True,
              "next_stage": "future_paper_observations_only"}
    return report, state


def main():
    now = datetime.now(timezone.utc)
    report, state = build(now, read(CANDLES), read(KNOWLEDGE), read(STATE))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Autonomous hypothesis architect:", report["archived_candidates"],
          "archived,", len(report["new_candidate_ids"]), "new;",
          len(report["issues"]), "issues")


if __name__ == "__main__":
    main()
