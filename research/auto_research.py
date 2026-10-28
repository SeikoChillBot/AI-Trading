"""Automatic, read-only trading research for Seiko Lab.

This tool does not optimize, backfill, or modify any running portfolio.
It examines the two independent $20 paper cohorts, rejects unsupported
performance conclusions, and records testable research hypotheses.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
CRYPTO_PATH = REPORTS / "realistic_metrics.json"
MULTI_PATH = REPORTS / "multi_asset_micro_metrics.json"
OUTPUT_JSON = REPORTS / "autonomous_research.json"
OUTPUT_MD = REPORTS / "autonomous_research.md"
HISTORY = REPORTS / "autonomous_research_history.jsonl"
INITIAL = 20.0
EXPECTED_ROBOTS = 18


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def finite_number(value, default=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def inspect_lab(kind: str, source: dict | None) -> dict:
    if not isinstance(source, dict):
        return {"lab": kind, "state": "source_missing", "eligible": 0,
                "strategies": [], "count": 0, "issues": ["Rapport absent ou illisible."]}
    rows = source.get("strategies")
    expected_model = "realistic_v2" if kind == "crypto" else "multi_asset_micro_v2"
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROBOTS or source.get("model") != expected_model:
        return {"lab": kind, "state": "invalid_source", "eligible": 0,
                "strategies": [], "count": 0,
                "issues": ["Rapport incomplet : modèle ou nombre de robots non conforme."]}
    names = [r.get("strategy") for r in rows if isinstance(r, dict)]
    if len(set(names)) != EXPECTED_ROBOTS or None in names:
        return {"lab": kind, "state": "invalid_source", "eligible": 0,
                "strategies": [], "count": 0,
                "issues": ["Identifiants de stratégies manquants ou dupliqués."]}
    age = finite_number(source.get("elapsed_days"), 0)
    minimum_days = 14 if kind == "crypto" else 30
    minimum_trades = 20
    details = []
    issues = []
    for row in rows:
        capital = finite_number(row.get("capital_usd"))
        ret = finite_number(row.get("return_pct"))
        dd = finite_number(row.get("max_observed_drawdown_pct"))
        completed = int(finite_number(row.get(
            "completed_roundtrips" if kind == "crypto" else "closed_roundtrips"), 0))
        fees = finite_number(row.get("fees_paid_usd" if kind == "crypto" else "fees_usd"), 0)
        observed = int(finite_number(row.get(
            "observation_count" if kind == "crypto" else "observations"), 0))
        price_quality = str(row.get("pricing_quality") or "") if kind == "multi" else "simulated_kraken"
        valid = capital is not None and capital >= 0 and ret is not None and dd is not None
        enough = valid and age >= minimum_days and completed >= minimum_trades
        if kind == "multi" and price_quality in ("NO_DATA", "STALE", "UNKNOWN", ""):
            enough = False
        details.append({
            "strategy": row["strategy"], "asset": row.get("asset"),
            "capital_usd": round(capital, 5) if capital is not None else None,
            "net_return_pct": round(ret, 4) if ret is not None else None,
            "drawdown_pct": round(dd, 4) if dd is not None else None,
            "completed_roundtrips": completed, "observations": observed,
            "fees_paid_usd": round(fees, 5),
            "pricing_quality": price_quality, "ready_for_review": bool(enough),
            "confidence": "requires_out_of_sample_validation" if enough else "insufficient_sample",
            "excess_vs_hold_pct_points": (
                finite_number(row.get("excess_vs_hold_pct_points")) if kind == "crypto" else None),
        })
        if not valid:
            issues.append("Données invalides pour " + row["strategy"])
    total = finite_number(source.get(
        "latest_total_usd" if kind == "crypto" else "capital_usd"))
    if total is None:
        issues.append("Capital total indisponible.")
    if age < minimum_days:
        issues.append("Historique trop court : %.3f jour(s), minimum de revue %d." % (age, minimum_days))
    eligible = [r for r in details if r["ready_for_review"]]
    fees_total = round(sum(r["fees_paid_usd"] for r in details), 5)
    return {
        "lab": kind, "state": "data_available", "count": len(details),
        "started_at": source.get("started_at"), "updated_at": source.get("updated_at"),
        "elapsed_days": age, "minimum_days_for_review": minimum_days,
        "minimum_closed_trades_for_review": minimum_trades,
        "initial_usd": INITIAL * len(details),
        "estimated_current_usd": total,
        "fees_paid_usd": fees_total,
        "eligible": len(eligible),
        "strategies": details, "issues": issues,
    }


def hypotheses(labs: dict) -> list[dict]:
    result = [
        {"id": "COST-STRESS-001", "domain": "crypto",
         "title": "Éprouver la sensibilité des robots courts aux frais",
         "why": "Avec des mises de 20 $, le coût aller-retour peut dominer le signal.",
         "experiment": "Rejouer exactement les mêmes signaux avec frais actuels, +50 % et +100 %, en période hors échantillon.",
         "success_rule": "Comparer rendement net, drawdown et nombre de positions ; ne pas promouvoir une variante sur le seul gain brut.",
         "state": "hypothesis_only_no_test"},
        {"id": "THRESHOLD-002", "domain": "crypto",
         "title": "Étudier des seuils d'entrée plus sélectifs",
         "why": "Un seuil plus exigeant peut réduire la rotation et les frais, mais aussi manquer des tendances.",
         "experiment": "Comparer à règles fixes les seuils actuels, plus stricts et moins stricts sur plusieurs fenêtres chronologiques disjointes.",
         "success_rule": "Conserver un témoin inchangé, pénaliser la complexité et regarder le rendement net hors échantillon.",
         "state": "hypothesis_only_no_test"},
        {"id": "SMA-003", "domain": "multi",
         "title": "Comparer SMA10, SMA20 et SMA40 en actions / ETF",
         "why": "La bonne fréquence dépend des coûts et de l'actif ; aucune période optimale n'est connue aujourd'hui.",
         "experiment": "Backtests chronologiques par marché, dividendes et opérations sur titres correctement intégrés, puis paper trading prospectif.",
         "success_rule": "Ne sélectionner aucune combinaison sans données de prix fiables et validation hors échantillon.",
         "state": "blocked_until_data_quality_confirmed"},
        {"id": "FRACTIONS-004", "domain": "multi",
         "title": "Valider les ordres fractionnés de 20 $ chez un courtier réel",
         "why": "Les fractions d'ETF US et les minima de courtage ne sont pas vérifiés pour un compte en France.",
         "experiment": "Contrôler l'instrument, la permission du courtier, le minimum d'ordre, la commission et la disponibilité européenne.",
         "success_rule": "N'afficher comme exécutable que ce qu'un courtier de référence accepte effectivement.",
         "state": "blocked_until_broker_verified"},
        {"id": "BASELINE-005", "domain": "multi",
         "title": "Ajouter DCA, conservation et liquidités comme témoins",
         "why": "Une stratégie active doit battre un témoin réaliste après frais, pour un risque comparable.",
         "experiment": "Comparer les trajectoires aux mêmes dates et sur le même actif, sans utiliser les cours futurs.",
         "success_rule": "Comparer rendement total net, temps investi et drawdown, sans fusionner les cohortes.",
         "state": "hypothesis_only_no_test"},
    ]
    if labs["crypto"].get("eligible", 0) == 0 and labs["multi"].get("eligible", 0) == 0:
        result.insert(0, {
            "id": "WAIT-000", "domain": "all",
            "title": "Priorité : observer sans modifier les stratégies",
            "why": "Aucune des deux cohortes ne possède encore assez de transactions clôturées et de recul temporel.",
            "experiment": "Accumuler des observations horodatées et vérifier que les données ne sont pas manquantes ou recalculées rétroactivement.",
            "success_rule": "Garder les 36 robots de référence inchangés et préparer des challengers indépendants.",
            "state": "active_research_gate",
        })
    return result


def build_report(crypto: dict | None, multi: dict | None, now: datetime) -> dict:
    labs = {"crypto": inspect_lab("crypto", crypto),
            "multi": inspect_lab("multi", multi)}
    ready = sum(x["eligible"] for x in labs.values())
    blocked = [
        "Aucune promesse de rentabilité, d'alpha ou de revenu mensuel.",
        "Aucune modification des stratégies en cours ou des anciens historiques.",
        "Aucun ordre réel, effet de levier ou connexion courtier.",
        "Une optimisation future doit être vérifiée hors échantillon (walk-forward).",
        "Les ETF US fractionnés et les taux BCE ne démontrent pas l'exécutabilité chez un courtier.",
    ]
    return {
        "schema": 1,
        "generated_at": now.astimezone(timezone.utc).isoformat(),
        "research_date_utc": now.astimezone(timezone.utc).date().isoformat(),
        "kind": "deterministic_statistical_research",
        "llm_connected": False,
        "autonomous_strategy_changes_enabled": False,
        "real_trading_enabled": False,
        "qualification": {
            "ready_for_human_review": ready,
            "proven_profitable": 0,
            "warning": "Une revue statistique ne prouve pas une rentabilité future.",
        },
        "labs": labs,
        "hypotheses": hypotheses(labs),
        "safety_guards": blocked,
    }


def as_markdown(report: dict) -> str:
    lines = [
        "# Seiko Trading Lab — Recherche automatique",
        "",
        "Date UTC : " + report["generated_at"],
        "",
        "**État : analyse statistique automatique, IA générative non connectée.**",
        "**Aucune stratégie modifiée ni aucun ordre réel.**",
        "",
        "## Données observées",
    ]
    for key in ("crypto", "multi"):
        lab = report["labs"][key]
        if lab["state"] != "data_available":
            lines.append("- **%s** : %s." % (key, lab["state"]))
            continue
        lines.append(
            "- **%s** : %d robots, %.3f jour(s) de données, %.2f $ fictifs de référence, %.4f $ de frais déjà enregistrés, **%d éligibles à une revue**."
            % (key, lab["count"], lab["elapsed_days"], lab["initial_usd"],
               lab["fees_paid_usd"], lab["eligible"])
        )
    lines.extend([
        "", "**Conclusion : %d stratégie(s) suffisamment documentée(s) pour une revue ; aucune rentabilité démontrée.**"
        % report["qualification"]["ready_for_human_review"],
        "", "## Hypothèses proposées (non testées)",
    ])
    for proposal in report["hypotheses"]:
        lines.extend([
            "", "### " + proposal["id"] + " — " + proposal["title"],
            "- Pourquoi : " + proposal["why"],
            "- Expérience : " + proposal["experiment"],
            "- Condition de validation : " + proposal["success_rule"],
            "- Statut : " + proposal["state"],
        ])
    lines.extend(["", "## Limites et règles",
                  *("- " + guard for guard in report["safety_guards"]),
                  "", "Le modèle génératif éventuel doit formuler des hypothèses, non voter une modification des robots actifs.",
                  ""])
    return "\n".join(lines)


def write_once_per_day(report: dict) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    previous = []
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
                if entry.get("research_date_utc") != report["research_date_utc"]:
                    previous.append(entry)
            except ValueError:
                continue
    digest = {
        "research_date_utc": report["research_date_utc"],
        "generated_at": report["generated_at"],
        "crypto_eligible": report["labs"]["crypto"]["eligible"],
        "multi_eligible": report["labs"]["multi"]["eligible"],
        "crypto_current_usd": report["labs"]["crypto"].get("estimated_current_usd"),
        "multi_current_usd": report["labs"]["multi"].get("estimated_current_usd"),
        "tested_hypotheses": 0,
        "active_strategy_changes": 0,
    }
    previous.append(digest)
    HISTORY.write_text(
        "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in previous),
        encoding="utf-8",
    )


def main() -> None:
    now = datetime.now(timezone.utc)
    report = build_report(read_json(CRYPTO_PATH), read_json(MULTI_PATH), now)
    REPORTS.mkdir(exist_ok=True, parents=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(as_markdown(report), encoding="utf-8")
    write_once_per_day(report)
    print("Research evaluated %d paper robots; %d qualified for review, %d tested hypotheses"
          % (sum(lab["count"] for lab in report["labs"].values()),
             report["qualification"]["ready_for_human_review"], 0))


if __name__ == "__main__":
    main()
