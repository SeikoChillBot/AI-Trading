"""Persistent scientific memory of falsifiable AIT paper-only experiments.

Keeps unsuccessful hypotheses and their failed checks even after working
strategies rotate out. Never infers causal explanations or future profitability
from historical replay. Idempotent across repeated two-hour GitHub cycles.
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "state/strategy_knowledge_base.json"
FORWARD = ROOT / "state/strategy_forward_positions.json"
STATE = ROOT / "state/scientific_memory.json"
REPORT = ROOT / "reports/scientific_memory.json"
MAX_LESSONS = 500
MAX_FINGERPRINTS = 3500
MAX_PER_ID_HISTORY = 12


def read(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _numeric(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value), 5) if -100000 < value < 100000 else None


def research_agenda(counts, population):
    """Formulate competing, falsifiable NEXT studies from failures.

    A failed historical criterion is evidence about these historical tests,
    NOT a diagnosis of causal market behavior. Recommended experiments remain
    speculative until independent forward-paper comparisons accumulate.
    """
    proposals = [
        ("positive_with_double_costs", "cost_sensitivity",
         "Tester moins d'ordres et des confirmations de volatilité, mais surveiller une perte de signaux utiles.",
         "Comparer les règles simples et composées avec frais normaux/doublés sur des bougies futures."),
        ("enough_closed_trades", "trade_density",
         "Tester des fenêtres plus courtes et des filtres moins restrictifs sans supposer un meilleur profit.",
         "Rejeter les hypothèses dont l'échantillon futur reste insuffisant ou net négatif après frais."),
        ("positive_average_net", "net_return",
         "Comparer familles de tendance, retour vers moyenne et abstention sans sélectionner sur le contrôle historique.",
         "Conserver seulement les améliorations positives après frais sur de nouvelles journées distinctes."),
        ("beats_hold_in_most_folds", "hold_comparison",
         "Tester si un signal ajoute de la valeur au simple achat-conservation sur les mêmes dates.",
         "Rejeter la supériorité si le différentiel futur au témoin Hold n'est pas positif."),
        ("drawdown_under_20_pct", "drawdown",
         "Tester des confirmations prudentes et leur coût d'opportunité sans attribuer une cause aux pertes.",
         "Rejeter si le drawdown fictif prospectif excède le seuil ou si le gain net se détériore."),
    ]
    result = []
    for check, category, hypothesis, rejection in proposals:
        failures = int(counts.get(check, 0))
        if failures == 0:
            continue
        result.append({
            "category": category, "failed_historical_checks": failures,
            "historical_population": population,
            "hypothesis_to_falsify": hypothesis,
            "experiment": rejection,
            "independent_future_data_required": True,
            "causal_proof": False,
        })
    return sorted(result, key=lambda row: (-row["failed_historical_checks"], row["category"]))[:4]


def build(now, knowledge, forward, previous):
    prior = previous if isinstance(previous, dict) else {}
    retained = prior.get("lessons", [])
    retained = retained if isinstance(retained, list) else []
    known = {item["id"]: item for item in retained[-MAX_LESSONS:]
             if isinstance(item, dict) and isinstance(item.get("id"), str)}
    seen = [x for x in prior.get("seen_spec_ids", []) if isinstance(x, str) and len(x) == 18]
    unique = set(seen) | set(known)
    if (not isinstance(knowledge, dict) or knowledge.get("schema") != 1
            or knowledge.get("real_orders") is not False
            or knowledge.get("never_run_model_code") is not True
            or knowledge.get("promotions_enabled") is not False):
        return ({
            "schema": 1, "generated_at": now.isoformat(),
            "state": "invalid_research_input", "recorded_hypotheses": len(known),
            "new_revisions": 0, "real_orders": False, "robots_modified": False
        }, {"schema": 1, "lessons": list(known.values()),
            "seen_spec_ids": seen, "real_orders": False})
    trials = {}
    if (isinstance(forward, dict) and forward.get("schema") == 1
            and forward.get("real_orders") is False):
        trials = forward.get("tracks", {})
        trials = trials if isinstance(trials, dict) else {}
    new_revisions = 0
    for idea in knowledge.get("ideas", []) if isinstance(knowledge.get("ideas"), list) else []:
        if not isinstance(idea, dict) or not isinstance(idea.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(idea["spec"])
            key = foundry.identifier(spec)
        except (ValueError, TypeError, KeyError):
            continue
        if idea.get("id") != key or len(key) != 18:
            continue
        if key not in unique:
            seen.append(key)
            unique.add(key)
        previous_row = known.get(key, {})
        if not isinstance(previous_row, dict):
            previous_row = {}
        result = idea.get("latest_result", {})
        if not isinstance(result, dict):
            result = {}
        checks = result.get("checks", {})
        checks = checks if isinstance(checks, dict) else {}
        clean_failures = sorted(k for k, passed in checks.items()
                                if isinstance(k, str) and passed is False)[:10]
        digest = idea.get("latest_data_sha256")
        past_digests = previous_row.get("seen_data_sha256", [])
        past_digests = past_digests if isinstance(past_digests, list) else []
        revisions = int(previous_row.get("historical_revisions", 0))
        historical = previous_row.get("historical_snapshots", [])
        historical = historical[-MAX_PER_ID_HISTORY:] if isinstance(historical, list) else []
        if (isinstance(digest, str) and len(digest) == 64
                and digest not in past_digests):
            past_digests = (past_digests + [digest])[-MAX_PER_ID_HISTORY:]
            historical.append({
                "evidence_kind": "reused_historical_exploration",
                "observed_at": now.isoformat(),
                "data_sha256": digest,
                "net_pct": _numeric(result.get("average_net_pct")),
                "double_cost_net_pct": _numeric(result.get("average_double_cost_net_pct")),
                "excess_vs_hold": _numeric(result.get("average_excess_vs_hold_points")),
                "drawdown_pct": _numeric(result.get("max_drawdown_pct")),
                "failed_checks": clean_failures,
            })
            historical = historical[-MAX_PER_ID_HISTORY:]
            revisions += 1
            new_revisions += 1
        forward_old = previous_row.get("latest_prospective", {})
        forward_old = forward_old if isinstance(forward_old, dict) else {}
        rec = trials.get(key)
        future = forward_old
        if isinstance(rec, dict) and rec.get("id") == key:
            days = rec.get("observed_days")
            if (type(days) is int and days > 0
                    and rec.get("status") == "observing_paper_only"):
                future = {
                    "status": "observing_paper_only",
                    "observed_days": days,
                    "net_pct": _numeric(rec.get("net_pct")),
                    "excess_vs_hold_points": _numeric(rec.get("excess_vs_hold_points")),
                    "max_drawdown_pct": _numeric(rec.get("max_drawdown_pct")),
                    "closed_trades": rec.get("closed_trades", 0),
                    "last_closed_day": rec.get("last_t"),
                    "not_a_guarantee": True,
                }
        known[key] = {
            "id": key, "asset": spec["asset"], "logic": spec["logic"],
            "confirmations": spec.get("confirmations", []),
            "source": idea.get("source"),
            "first_seen_at": previous_row.get("first_seen_at", now.isoformat()),
            "last_reviewed_at": now.isoformat() if revisions > 0 else previous_row.get("last_reviewed_at"),
            "historical_revisions": revisions,
            "historical_snapshots": historical,
            "seen_data_sha256": past_digests,
            "latest_historical_failure_reasons": clean_failures,
            "latest_prospective": future,
            "hypothesis_only": True,
        }
    kept = list(known.values())[-MAX_LESSONS:]
    counts = Counter()
    by_logic = {}
    for row in kept:
        counts.update(row.get("latest_historical_failure_reasons", []))
        by_logic[row.get("logic")] = by_logic.get(row.get("logic"), 0) + 1
    # Retain fingerprints of dropped hypotheses: don't accidentally redo them.
    all_ids = list(dict.fromkeys(seen + [row["id"] for row in kept]))[-MAX_FINGERPRINTS:]
    state = {
        "schema": 1, "updated_at": now.isoformat(),
        "lessons": kept, "seen_spec_ids": all_ids,
        "real_orders": False, "robots_modified": False,
    }
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "state": "research_memory_recorded",
        "recorded_hypotheses": len(kept),
        "total_experiment_fingerprints": len(all_ids),
        "new_revisions": new_revisions,
        "failure_patterns": dict(counts.most_common(10)),
        "research_agenda": research_agenda(counts, len(kept)),
        "tested_logic_families": by_logic,
        "prospective_observed": sum(bool(x.get("latest_prospective", {}).get("observed_days"))
                                    for x in kept),
        "recent_lessons": [{
            "id": row["id"], "asset": row["asset"],
            "logic": row["logic"],
            "confirmations": row["confirmations"],
            "historical_failure_reasons": row["latest_historical_failure_reasons"][:5],
            "historical_revisions": row["historical_revisions"],
            "forward_observed_days": row.get("latest_prospective", {}).get("observed_days", 0),
        } for row in kept[-12:]],
        "no_causal_attribution": True,
        "historical_results_not_prospective_proof": True,
        "no_promotions": True,
        "real_orders": False, "robots_modified": False,
    }
    return report, state


def model_memory(report):
    if (not isinstance(report, dict) or report.get("schema") != 1
            or report.get("real_orders") is not False
            or report.get("no_causal_attribution") is not True):
        return {}
    return {
        "hypotheses_remembered": report.get("recorded_hypotheses", 0),
        "failure_counts_not_explanations": report.get("failure_patterns", {}),
        "recent_lessons": report.get("recent_lessons", [])[-8:],
        "priority_falsifiable_experiments": report.get("research_agenda", [])[:4],
        "study_rule": "Choose testable alternatives, never treat repeated historical fits as future proof.",
    }


def main():
    now = datetime.now(timezone.utc)
    result, state = build(now, read(KNOWLEDGE), read(FORWARD), read(STATE))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Scientific research memory:", result["recorded_hypotheses"],
          "hypotheses,", result["new_revisions"], "new historical observations")


if __name__ == "__main__":
    main()
