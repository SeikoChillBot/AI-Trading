"""Adversarial research controls for Gemini-origin strategies.

Competing mechanism is an explicitly LOCAL scientific counterproposal,
not a statement that Gemini itself generated the rival. Each comparison must
be registered before the first unseen candle; no historical backtest may
settle a prospective dispute.
"""
from __future__ import annotations

from research import strategy_foundry as foundry

ALTERNATIVES = {
    "trend_following": ("mean_reversion", "rsi_reversal"),
    "mean_reversion": ("trend_following", "breakout"),
    "breakout": ("mean_reversion", "volatility_gate"),
    "ema_trend": ("rsi_reversal", "breakout"),
    "rsi_reversal": ("ema_trend", "trend_following"),
    "volatility_gate": ("breakout", "mean_reversion"),
    "dual_confirmation": ("mean_reversion", "ema_trend"),
}


def competing_spec(primary, seen):
    """Create the closest untried *mechanistically distinct* control."""
    for logic in ALTERNATIVES[primary["logic"]]:
        for gates in ([], ["quiet_volatility"], ["positive_momentum"]):
            proposal = dict(primary)
            proposal["logic"] = logic
            proposal["confirmations"] = gates
            proposal["rationale"] = (
                "Explication concurrente à examiner sur les mêmes nouvelles "
                "journées et avec les mêmes frais, sans prétendre en connaître l'issue."
            )
            try:
                rival = foundry.normalise(proposal)
                key = foundry.identifier(rival)
            except (TypeError, ValueError, KeyError):
                continue
            if key not in seen and key != foundry.identifier(primary):
                return rival
    return None


def comparison(primary_record, control_record, forward):
    """Only compare two prospective tracks over the same completed interval."""
    if not isinstance(forward, dict) or forward.get("real_orders") is not False:
        return {"stage": "awaiting_synchronized_future", "observed_days": 0}
    tracks = forward.get("tracks", {})
    if not isinstance(tracks, dict):
        return {"stage": "awaiting_synchronized_future", "observed_days": 0}
    a = tracks.get(primary_record.get("id"))
    b = tracks.get(control_record.get("id"))
    if not isinstance(a, dict) or not isinstance(b, dict):
        return {"stage": "awaiting_synchronized_future", "observed_days": 0}
    from research.research_director import prospective_status
    stage_a, days_a = prospective_status(primary_record, forward)
    stage_b, days_b = prospective_status(control_record, forward)
    valid = {"tentatively_supported_paper_only", "prospectively_contradicted"}
    if (stage_a not in valid or stage_b not in valid
            or a.get("last_t") != b.get("last_t")
            or days_a != days_b or days_a < 90
            or primary_record.get("closed_day_at_registration")
            != control_record.get("closed_day_at_registration")):
        return {"stage": "awaiting_synchronized_future",
                "observed_days": min(days_a, days_b)}
    primary_net, control_net = a["net_pct"], b["net_pct"]
    diff = round(primary_net - control_net, 5)
    if diff > 0 and primary_net > 0 and a["excess_vs_hold_points"] > 0:
        state = "tentative_support_for_primary"
    elif diff <= 0:
        state = "control_at_least_as_good"
    else:
        state = "primary_better_than_control_but_not_profitable"
    return {
        "stage": state, "observed_days": days_a,
        "primary_net_pct": primary_net, "control_net_pct": control_net,
        "primary_minus_control_pct_points": diff,
        "comparison_evidence": "same_new_daily_candles_after_registration",
        "not_proof_of_future_profit": True,
    }
