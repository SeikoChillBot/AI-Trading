"""Bounded genetic-style mutation and honest failure memory for fictitious AIT.

A strategy is a frozen declarative genome. The mutation engine inspects historical
development results only, mutates one parameter at a time, and records why a
candidate was explored. No self-modifying Python, no real orders, no live
promotion. Future performance is measured by the separate forward experiment.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research import autonomous_optimizer as opt
from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
CANDLES = ROOT / "reports/challenger_candles.json"
OPTIMIZER = ROOT / "reports/autonomous_optimizer.json"
KNOWLEDGE = ROOT / "state/strategy_knowledge_base.json"
STATE = ROOT / "state/strategy_evolution.json"
REPORT = ROOT / "reports/strategy_evolution.json"
MAX_ARCHIVE = 40
PARENT_COUNT = 3
# Controlled range of candidate variants, with immutable specifications.
FIELDS = ("logic", "lookback_days", "threshold_pct", "max_hold_days")


def read(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def mutations(parent):
    parent = foundry.normalise(parent)
    for field, values in (
        ("logic", foundry.LOGICS),
        ("lookback_days", foundry.WINDOWS),
        ("threshold_pct", (0.5, 1., 2.)),
        ("max_hold_days", foundry.MAX_HOLD),
    ):
        for value in values:
            if value == parent[field]:
                continue
            new = dict(parent)
            new[field] = value
            new["rationale"] = (
                "Mutation contrôlée de " + field +
                " pour confronter une hypothèse historique au résultat de sa variante."
            )
            yield field, foundry.normalise(new)


def failure_diagnosis(result):
    if not isinstance(result, dict):
        return ["historical_evidence_missing"]
    metric = result.get("selection_metrics", {})
    later = result.get("historical_challenge", {})
    failed = []
    if metric.get("avg_net_pct", 0) <= 0:
        failed.append("development_net_negative")
    if metric.get("avg_double_cost_net_pct", 0) <= 0:
        failed.append("double_cost_sensitivity")
    if later.get("net_average_pct", 0) <= 0:
        failed.append("historical_challenge_negative")
    if not later.get("beats_hold_both", False):
        failed.append("historical_hold_not_beat_both")
    return failed or ["exploratory_only_no_prospective_validation"]


def build(now, bars_by_asset, optimizer, previous, knowledge):
    source = bars_by_asset if isinstance(bars_by_asset, dict) else {}
    prior = previous if isinstance(previous, dict) else {}
    known = {}
    for candidate in prior.get("candidates", [])[-MAX_ARCHIVE:]:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(candidate["spec"])
        except (ValueError, KeyError, TypeError):
            continue
        key = foundry.identifier(spec)
        if candidate.get("id") == key:
            known[key] = candidate
    tried = set(known)
    for row in knowledge.get("ideas", []) if isinstance(knowledge, dict) else []:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            tried.add(row["id"])
    history = []
    selected = {}
    refreshed = []
    events = []
    issues = {}
    source_valid = (isinstance(optimizer, dict) and optimizer.get("schema") == 1
                    and optimizer.get("source") == "autonomous_grid_search"
                    and optimizer.get("real_orders") is False
                    and optimizer.get("robot_changes") is False)
    by_id = {}
    if source_valid:
        for row in optimizer.get("candidates", []):
            if not isinstance(row, dict) or not isinstance(row.get("spec"), dict):
                continue
            try:
                spec = foundry.normalise(row["spec"])
                if row.get("id") == foundry.identifier(spec):
                    by_id[row["id"]] = row
            except (TypeError, ValueError, KeyError):
                pass
    last_search = dict(prior.get("last_search_closed_day", {})) if isinstance(
        prior.get("last_search_closed_day"), dict) else {}
    for asset in foundry.ASSETS:
        bars = source.get(asset)
        try:
            foundry.validate_bars(bars, now)
            parent_id = optimizer.get("latest_by_asset", {}).get(asset) if source_valid else None
            parent = by_id.get(parent_id)
            if parent is None or parent["spec"]["asset"] != asset:
                raise ValueError("missing_authenticated_parent")
            # A previously evolved genome becomes the parent of a new generation
            # only when its *development* score is better than the current
            # original optimizer candidate. The reused historical challenge
            # must NOT choose the parent (avoid selection on held-out labels).
            prior_child_id = prior.get("selected_by_asset", {}).get(asset)
            prior_child = known.get(prior_child_id)
            if (isinstance(prior_child, dict)
                    and prior_child.get("asset") == asset
                    and prior_child.get("source") == "bounded_evolution"
                    and isinstance(prior_child.get("selection_metrics"), dict)
                    and isinstance(parent.get("selection_metrics"), dict)
                    and prior_child["selection_metrics"].get("score", -1e9) >
                        parent["selection_metrics"].get("score", -1e9)):
                parent_id, parent = prior_child_id, prior_child
            last_t = bars[-1]["t"]
            prior_t = last_search.get(asset)
            recent = (type(prior_t) is int
                      and last_t - prior_t < opt.SEARCH_EVERY_CLOSED_DAYS * 86400)
            if recent and prior.get("selected_by_asset", {}).get(asset) in known:
                selected[asset] = prior["selected_by_asset"][asset]
                continue
            # One-parameter neighbor exploration; only development folds rank.
            parent_spec = foundry.normalise(parent["spec"])
            ranked = []
            for field, variant in mutations(parent_spec):
                identity = foundry.identifier(variant)
                if identity in tried or identity == parent_id:
                    continue
                score = opt.score_development(bars, variant)
                ranked.append((score["score"], identity, field, variant, score))
            if not ranked:
                events.append({"asset": asset, "status": "mutation_space_exhausted"})
                last_search[asset] = last_t
                continue
            best = sorted(ranked, key=lambda row: (-row[0], row[1]))[0]
            _, key, field, spec, fitness = best
            historical = opt.challenge(bars, spec)
            record = {
                "id": key, "asset": asset, "source": "bounded_evolution",
                "parent_id": parent_id, "changed_dimension": field,
                "generation": 1 + int(prior.get("generation_by_asset", {}).get(asset, 0)),
                "spec": spec, "selection_metrics": fitness,
                "historical_challenge": historical,
                "parent_failure_reasons": failure_diagnosis(parent),
                "eligible_for_live_trading": False,
                "historical_candidate_only": True,
                "created_at": now.isoformat(),
                "frozen_at_closed_day": last_t,
            }
            known[key] = record
            tried.add(key)
            refreshed.append(key)
            selected[asset] = key
            last_search[asset] = last_t
            events.append({"asset": asset, "id": key, "parent": parent_id,
                           "status": "mutation_created",
                           "tested_variants": len(ranked), "dimension": field})
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            issues[asset] = str(error)[:75]
            key = prior.get("selected_by_asset", {}).get(asset)
            if key in known:
                selected[asset] = key
    records = list(known.values())[-MAX_ARCHIVE:]
    ids = {x["id"] for x in records}
    selected = {key: val for key, val in selected.items() if val in ids}
    generations = dict(prior.get("generation_by_asset", {})) if isinstance(
        prior.get("generation_by_asset"), dict) else {}
    for item in records:
        generations[item["asset"]] = max(generations.get(item["asset"], 0),
                                         int(item.get("generation", 0)))
    state = {
        "schema": 1, "updated_at": now.isoformat(),
        "candidates": records, "selected_by_asset": selected,
        "last_search_closed_day": last_search, "generation_by_asset": generations,
        "real_orders": False, "robot_changes": False,
    }
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "source": "bounded_evolution",
        "real_orders": False, "robot_changes": False,
        "total_mutations": len(records), "new_candidate_ids": refreshed,
        "selected_by_asset": selected, "candidates": records,
        "events": events, "issues": issues,
        "lesson": "A mutation addresses observed historical weaknesses, not proof that the weakness is cured.",
        "no_automatic_live_promotion": True,
    }
    return report, state


def main():
    now = datetime.now(timezone.utc)
    report, state = build(now, read(CANDLES), read(OPTIMIZER), read(STATE), read(KNOWLEDGE))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Autonomous evolution:", report["total_mutations"],
          "cumulative mutations,", len(report["new_candidate_ids"]), "new," ,
          "issues:", len(report["issues"]))


if __name__ == "__main__":
    main()
