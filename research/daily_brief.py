"""Daily Seiko laboratory journal, grounded only in observed reports.

No additional paid/free model calls. Model-authored notes are attributed to
Gemini ONLY when an actual successful API response for that date is evidenced.
All other summaries are deterministic, with explicit data provenance.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PARIS = ZoneInfo("Europe/Paris")
OUTPUT = ROOT / "reports/ai_daily_brief.json"
STATE = ROOT / "state/ai_daily_brief_state.json"
SOURCES = {
    "model": "reports/ai_research_status.json",
    "proposals": "reports/ai_research_proposals.json",
    "journal": "state/ai_journal_state.json",
    "evolution": "reports/robot_evolution.json",
    "experiments": "reports/ai_placement_experiments.json",
    "intraday": "reports/intraday_research.json",
    "news": "reports/market_news.json",
    "whales": "reports/large_transfer_observations.json",
}
EVENT_LOG = ROOT / "reports/robot_evolution_events.jsonl"


def read(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def date_of(timestamp):
    try:
        value = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return value.astimezone(PARIS).date().isoformat() if value.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def events_from_lines(text):
    events = []
    for line in text.splitlines()[-800:]:
        try:
            item = json.loads(line)
            if isinstance(item, dict) and isinstance(item.get("at"), str):
                events.append(item)
        except (ValueError, TypeError):
            continue
    return events


def create_day(now, sources, historical_events):
    day = now.astimezone(PARIS).date().isoformat()
    journal = sources.get("journal", {})
    stored = journal.get("entries", [])
    todays_entries = [
        item for item in stored
        if isinstance(item, dict) and date_of(item.get("at")) == day
    ] if isinstance(stored, list) else []
    ai_notes = [entry for entry in todays_entries if entry.get("type") == "ai_note"]
    news_entries = [entry for entry in todays_entries if entry.get("type") == "news"]
    own_events = [event for event in historical_events if date_of(event.get("at")) == day]
    gemini_proposals = [e for e in own_events if e.get("action") == "proposed_by_gemini"]
    quant_proposals = [e for e in own_events if e.get("action") == "proposed_by_quant_engine"]
    promotions = [e for e in own_events if e.get("action") == "paper_tuning_activated"]
    rollbacks = [e for e in own_events if e.get("action") == "paper_tuning_rolled_back"]
    model = sources.get("model", {})
    model_today = date_of(model.get("generated_at")) == day
    latest_model_state = model.get("state") if model_today else "unverified_for_day"
    actual_ai = next((e for e in ai_notes if e.get("title") == "Analyse Gemini — synthèse"), None)
    model_summary = str(actual_ai.get("details", ""))[:620] if actual_ai else None

    experiments = sources.get("experiments", {})
    trials = experiments.get("trials", [])
    todays_trials = [t for t in trials if isinstance(t, dict)
                     and date_of(t.get("created_at")) == day] if isinstance(trials, list) else []
    from_gemini = sum(t.get("actor") == "gemini_structured_decision" for t in todays_trials)
    from_quant = sum(t.get("actor") == "quantitative_auto_fallback" for t in todays_trials)
    finished = sum(e.get("type") == "paper_test" and
                   "terminé" in str(e.get("title", "")).lower()
                   for e in todays_entries)

    studies = sources.get("intraday", {})
    study_today = date_of(studies.get("generated_at")) == day
    hourly_assets = studies.get("assets", {})
    hourly_count = len(hourly_assets) if study_today and isinstance(hourly_assets, dict) else 0
    better = sum(
        isinstance(info, dict)
        and isinstance(info.get("historical_study", {}).get("avg_excess_vs_hold"), (int, float))
        and info["historical_study"]["avg_excess_vs_hold"] > 0
        for info in hourly_assets.values()
    ) if hourly_count else 0

    registry = sources.get("evolution", {})
    registry_today = date_of(registry.get("generated_at")) == day
    counts = registry.get("counts", {}) if registry_today else {}
    whale_report = sources.get("whales", {})
    whale_fresh = date_of(whale_report.get("generated_at")) == day
    sample_count = sum(int(v) for v in whale_report.get("sampled_records", {}).values()
                       if type(v) is int and v >= 0) if whale_fresh else None

    researches = []
    if hourly_count:
        researches.append(
            f"Études horaires BTC/ETH/SOL : {hourly_count} actif(s) étudié(s) sur bougies Kraken clôturées ; "
            f"{better} avec un excès moyen historique positif face au Hold. "
            "Ces mesures ne prouvent pas un rendement futur."
        )
    if sample_count is not None:
        researches.append(
            f"Surveillance on-chain : {sample_count} transfert(s) publics échantillonnés sur USDC/USDT. "
            "Ni identité des baleines ni achat confirmé."
        )
    if news_entries:
        researches.append(
            f"Veille économique : {len(news_entries)} publication(s) sourcée(s) présentes dans le journal."
        )
    if not researches:
        researches.append("Aucune nouvelle collecte fiable documentée dans les rapports de cette journée.")

    decisions = []
    if gemini_proposals:
        decisions.append(f"Gemini : {len(gemini_proposals)} proposition(s) de variante robot enregistrée(s).")
    if quant_proposals:
        decisions.append(f"Moteur quantitatif : {len(quant_proposals)} variante(s) robot ouverte(s) en comparaison prospective.")
    if todays_trials:
        decisions.append(
            f"Placement fictif : {len(todays_trials)} essai(s) lancé(s) aujourd'hui "
            f"({from_gemini} initié(s) par Gemini, {from_quant} par moteur statistique)."
        )
    if promotions:
        decisions.append(f"{len(promotions)} réglage(s) fictif(s) activé(s) après contrôles.")
    if rollbacks:
        decisions.append(f"{len(rollbacks)} retour(s) automatique(s) à un réglage précédent.")
    if not decisions:
        decisions.append("Aucune nouvelle décision de placement ou modification confirmée aujourd'hui.")

    conclusions = []
    if model_summary:
        conclusions.append("Conclusion réellement publiée par Gemini : " + model_summary)
    elif latest_model_state == "model_reflection_failed":
        conclusions.append(
            "Aucun nouveau compte rendu Gemini confirmé pour cette journée : échec API enregistré ; "
            "la recherche statistique reste indépendante."
        )
    else:
        conclusions.append("Aucune nouvelle conclusion Gemini vérifiée pour cette journée.")
    if registry_today:
        conclusions.append(
            f"Robots : {int(counts.get('testing') or 0)} variante(s) en test, "
            f"{int(counts.get('activated') or 0)} réglage(s) activé(s) après validation."
        )
    if finished:
        conclusions.append(f"{finished} expérience(s) fictive(s) achevée(s) dans le journal.")
    else:
        conclusions.append("Aucun résultat final de placement fictif documenté aujourd'hui.")

    return {
        "date": day,
        "updated_at": now.isoformat(),
        "period": "in_progress",
        "headline": f"Bilan du {now.astimezone(PARIS).strftime('%d/%m/%Y')} — laboratoire de simulation",
        "source": "verified_reports_and_recorded_events",
        "gemini_authored_summary": model_summary,
        "gemini_status": latest_model_state,
        "research": researches[:6],
        "decisions": decisions[:8],
        "conclusions": conclusions[:5],
        "next": "Continuer les observations prospectives, contrôler frais et risques, et n'activer aucun réglage sans validation.",
        "counts": {
            "new_paper_trials": len(todays_trials),
            "gemini_trials": from_gemini,
            "quant_trials": from_quant,
            "quant_robot_proposals": len(quant_proposals),
            "gemini_robot_proposals": len(gemini_proposals),
            "activated_robot_changes": len(promotions),
            "news_articles_in_journal": len(news_entries),
        },
        "real_orders": False,
    }


def build(now, sources, events, previous):
    today = create_day(now, sources, events)
    days = previous.get("days", [])
    existing = {
        day["date"]: dict(day) for day in days
        if isinstance(day, dict) and isinstance(day.get("date"), str)
        and day.get("real_orders") is False and day.get("date") <= today["date"]
    } if isinstance(days, list) else {}
    for date, item in existing.items():
        if date < today["date"]:
            item["period"] = "closed_snapshot"
    existing[today["date"]] = today
    records = [existing[k] for k in sorted(existing, reverse=True)[:30]]
    report = {
        "schema": 1, "generated_at": now.isoformat(),
        "timezone": "Europe/Paris", "days": records,
        "automatic": True, "human_approval_required": False,
        "model_authorship_must_be_verified": True,
        "real_orders": False,
        "warning": "Récapitulatif de recherches et simulations. Les chiffres ne constituent pas des gains réels.",
    }
    return report, {"schema": 1, "days": records}


def main():
    now = datetime.now(timezone.utc)
    sources = {name: read(ROOT / path) for name, path in SOURCES.items()}
    try:
        lines = EVENT_LOG.read_text(encoding="utf-8")
    except OSError:
        lines = ""
    report, state = build(now, sources, events_from_lines(lines), read(STATE))
    for path, value in ((OUTPUT, report), (STATE, state)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Daily verified research journal", report["days"][0]["date"],
          "model status", report["days"][0]["gemini_status"])


if __name__ == "__main__":
    main()
