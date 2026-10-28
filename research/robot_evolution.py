"""Autonomous, auditable per-robot adaptation without LLM code execution.

Gemini may propose one of two preapproved parameter variants. The service opens
an independent forward-only comparison, measures both versions after fees and
can switch a paper robot ONLY after independent prospective validation.
Never changes strategy source, real brokers, $20 seed, or historical results.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from research.robot_tuning import (
    ALL_ROBOTS, TUNABLE_CRYPTO, TUNABLE_MULTI, CRYPTO_HOLD, MULTI_HOLD,
    active_scales, ALLOWED_SCALES,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "reports/autonomous_research.json"
IDEAS = ROOT / "reports/ai_research_proposals.json"
SHADOW = ROOT / "reports/robot_shadow_observations.json"
STATE = ROOT / "state/robot_evolution_state.json"
ACTIVE = ROOT / "state/robot_tuning_active.json"
OUTPUT = ROOT / "reports/robot_evolution.json"
EVENTS = ROOT / "reports/robot_evolution_events.jsonl"
MIN_PROSPECTIVE_DAYS = {"crypto":14, "multi":30}
MIN_ROUNDTRIPS = 20
MIN_GAIN_VS_CONTROL_POINTS = 2
MAX_DRAWDOWN_PCT = 15


def read(path, default=None):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else (default or {})
    except (OSError, ValueError):
        return default or {}


def valid_gemini_adjustments(ideas, robots):
    if (ideas.get("source") != "gemini_generate_content"
            or ideas.get("state") != "model_reflection_completed"):
        return []
    items = ideas.get("bot_adjustments", [])
    if not isinstance(items, list):
        return []
    seen = set()
    accepted = []
    for item in items[:3]:
        if not isinstance(item, dict):
            continue
        name = item.get("strategy")
        scale = item.get("entry_scale")
        reason = item.get("reason")
        if (name not in (TUNABLE_CRYPTO | TUNABLE_MULTI) or name not in robots
                or name in seen or type(scale) not in (int, float)
                or float(scale) not in (0.8, 1.2)
                or not isinstance(reason, str) or not 12 <= len(reason.strip()) <= 450):
            continue
        seen.add(name)
        accepted.append({"strategy":name, "entry_scale":float(scale),
                         "reason":reason.strip(), "source":"gemini_structured_hypothesis"})
    return accepted


def sufficient_prospective(evidence, candidate, now):
    """Deny promotion unless fresh, independent and fee-aware candidate evidence."""
    if not isinstance(evidence, dict):
        return False, ["missing_forward_shadow_data"]
    if (evidence.get("source") != "independent_forward_shadow_v1"
            or evidence.get("entry_scale") != candidate.get("entry_scale")
            or evidence.get("created_at") != candidate.get("created_at")
            or evidence.get("ready_for_real_orders") is not False):
        return False, ["shadow_provenance_or_candidate_mismatch"]
    try:
        age = (now-datetime.fromisoformat(candidate["created_at"])).total_seconds()/86400
        updated = datetime.fromisoformat(evidence["observed_at"])
        if updated.tzinfo is None or not 0 <= (now-updated).total_seconds() <= 8*3600:
            return False, ["stale_shadow_evidence"]
        lab = candidate["lab"]
        control = evidence["control"]
        variant = evidence["candidate"]
        checks = {
            "minimum_elapsed_days": age >= MIN_PROSPECTIVE_DAYS[lab],
            "minimum_closed_roundtrips": int(variant["closed_trades"]) >= MIN_ROUNDTRIPS,
            "sufficient_distinct_future_candles": int(evidence["observations"]) >= (120 if lab=="crypto" else 24),
            "improves_net_after_costs": (
                float(variant["net_return_pct"])-float(control["net_return_pct"])
                >= MIN_GAIN_VS_CONTROL_POINTS
                and float(variant["net_return_pct"]) > 0),
            "double_fees_not_loss": float(variant["stress_net_return_pct"]) > 0,
            "bounded_maximum_drawdown": (
                float(variant["max_drawdown_pct"]) <= MAX_DRAWDOWN_PCT
                and float(variant["max_drawdown_pct"]) <= float(control["max_drawdown_pct"])),
        }
        return all(checks.values()), [key for key, passed in checks.items() if not passed]
    except (KeyError, ValueError, TypeError, OverflowError):
        return False, ["incomplete_or_invalid_shadow_statistics"]


def build(now, research, ideas, shadow, state, active):
    labs = research.get("labs", {})
    robots = {}
    for lab in ("crypto", "multi"):
        for item in labs.get(lab, {}).get("strategies", []):
            name = item.get("strategy")
            if name in ALL_ROBOTS and name not in robots:
                robots[name] = {"lab":lab, "stats":item}
    proposals = valid_gemini_adjustments(ideas, robots)
    candidates = dict(state.get("candidates", {})) if isinstance(state.get("candidates", {}), dict) else {}
    profiles = dict(active.get("profiles", {})) if isinstance(active.get("profiles", {}), dict) else {}
    events = []
    for p in proposals:
        name = p["strategy"]
        if name in candidates or name in profiles:
            continue
        created = now.isoformat()
        candidate = {"strategy":name, "lab":robots[name]["lab"],
                     "created_at":created, "entry_scale":p["entry_scale"],
                     "from_scale":1.0, "reason":p["reason"],
                     "source":p["source"], "status":"shadow_pending",
                     "last_review":created, "failed_checks":["missing_forward_shadow_data"]}
        candidates[name] = candidate
        events.append({"at":created, "robot":name, "action":"proposed_by_gemini",
                       "from_scale":1.0, "to_scale":p["entry_scale"],
                       "details":"Shadow validation required before any change"})
    fresh_shadow = shadow.get("assets", {}) if isinstance(shadow.get("assets", {}), dict) else {}
    for name, candidate in candidates.items():
        if candidate.get("status") != "shadow_pending":
            continue
        evidence = fresh_shadow.get(name)
        permitted, fails = sufficient_prospective(evidence, candidate, now)
        candidate["failed_checks"] = fails
        candidate["last_review"] = now.isoformat()
        if permitted:
            # Parameter-only, never arbitrary AI source code, no real orders.
            profiles[name] = {
                "entry_scale":candidate["entry_scale"], "approved_at":now.isoformat(),
                "source":"automatic_prospective_validation",
                "from_scale":candidate["from_scale"],
                "evidence":"reports/robot_shadow_observations.json",
                "reason":"Net after costs, fee stress and max drawdown gates passed",
            }
            candidate["status"] = "automatically_promoted_paper_only"
            events.append({"at":now.isoformat(),"robot":name,"action":"paper_tuning_activated",
                           "from_scale":candidate["from_scale"],
                           "to_scale":candidate["entry_scale"],
                           "details":"Validated independent prospective shadow; no real orders"})
    listed = []
    for name in sorted(ALL_ROBOTS):
        lab = "crypto" if name in CRYPTO_HOLD | TUNABLE_CRYPTO else "multi"
        raw = robots.get(name, {})
        stat = raw.get("stats", {})
        current = profiles.get(name, {})
        approved = current.get("source")=="automatic_prospective_validation"
        proposed = candidates.get(name)
        control = name in CRYPTO_HOLD | MULTI_HOLD
        listed.append({
            "strategy":name, "lab":lab, "asset":stat.get("asset"),
            "role":"immutable_hold_benchmark" if control else "tunable_paper_robot",
            "current_entry_scale":float(current.get("entry_scale", 1.0)) if approved else 1.0,
            "mode":"hold" if control else name.rsplit("_", 1)[-1],
            "status":("baseline_held" if control else
                      "tuning_activated" if approved else
                      "testing_proposal" if proposed else "analyzing_for_opportunities"),
            "gemini_decision": (proposed or {}).get("reason"),
            "proposed_entry_scale":(proposed or {}).get("entry_scale"),
            "proposed_at":(proposed or {}).get("created_at"),
            "blocked_checks":(proposed or {}).get("failed_checks", []),
            "paper_return_pct":stat.get("net_return_pct"),
            "drawdown_pct":stat.get("drawdown_pct"),
            "closed_roundtrips":stat.get("completed_roundtrips"),
            "samples":stat.get("observations"),
            "ready_for_review":stat.get("ready_for_review") is True,
            "last_change_at":current.get("approved_at") if approved else None,
            "has_real_orders":False,
        })
    output = {
        "schema":1, "generated_at":now.isoformat(),
        "model":"per_robot_review_and_guarded_paper_evolution_v1",
        "description":"Every one of the 36 robots tracked individually; adaptive settings require independent shadow evidence.",
        "robots":listed, "counts":{
            "tracked":len(listed),
            "immutable_benchmarks":sum(x["role"]=="immutable_hold_benchmark" for x in listed),
            "testing":sum(x["status"]=="testing_proposal" for x in listed),
            "activated":sum(x["status"]=="tuning_activated" for x in listed),
        },
        "events_this_cycle":events,
        "max_simulated_start_per_robot_usd":20,
        "preserve_original_histories":True,
        "real_orders":False,
        "llm_generated_code_executed":False,
        "no_unverified_profit_claim":True,
    }
    return output, {"schema":1,"candidates":candidates}, {"schema":1,"profiles":profiles}, events


def main():
    now = datetime.now(timezone.utc)
    output, state, active, events = build(now, read(RESEARCH), read(IDEAS),
                                          read(SHADOW), read(STATE), read(ACTIVE))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    ACTIVE.write_text(json.dumps(active, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    if events:
        with EVENTS.open("a", encoding="utf-8") as stream:
            for event in events:
                stream.write(json.dumps(event, ensure_ascii=False)+"\n")
    print("Robot evolution", output["counts"], "new transitions", len(events))


if __name__ == "__main__":
    main()
