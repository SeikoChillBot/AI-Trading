"""Prospective paper-only evaluation of frozen research strategy specifications.

On registration, the last completed Kraken daily candle establishes a baseline.
Only subsequently observed completed candles may advance a virtual position.
No backfilled missed executions, no model-supplied code and no real orders.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from research import strategy_foundry as foundry

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "state/strategy_knowledge_base.json"
CANDLES = ROOT / "reports/challenger_candles.json"
STATE = ROOT / "state/strategy_forward_positions.json"
REPORT = ROOT / "reports/strategy_forward.json"
MAX_TRACKED = 24
CAPITAL = foundry.CAPITAL
COST = foundry.COST


def read(path):
    try:
        x = json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def register(idea, bars, now):
    spec = foundry.normalise(idea["spec"])
    foundry.validate_bars(bars, now)
    return {
        "id": foundry.identifier(spec),
        "source": idea.get("source"), "spec": spec,
        "started_at": now.isoformat(), "last_t": bars[-1]["t"],
        "observed_days": 0, "closed_trades": 0,
        "orders": 0, "holding_days": 0, "cash_usd": CAPITAL,
        "units": 0., "hold_units": None,
        "peak_usd": CAPITAL, "max_drawdown_pct": 0.,
        "status": "awaiting_new_daily_candle",
    }


def advance(record, bars):
    """Do not use a candle that was available before initial registration."""
    spec = foundry.normalise(record["spec"])
    last = record["last_t"]
    if type(last) is not int:
        raise ValueError("invalid_state_timestamp")
    matches = [i for i, bar in enumerate(bars) if bar["t"] == last]
    if len(matches) != 1:
        record["status"] = "paused_missing_prior_candle"
        return record
    i = matches[0]
    if i == len(bars) - 1:
        return record
    if len(bars) - i - 1 != 1 or bars[i + 1]["t"] != last + 86400:
        # Never pretend to have traded on missed historical sessions.
        record["status"] = "paused_missing_forward_observation"
        return record
    new = bars[i + 1]
    if i + 1 < max(42, spec["lookback_days"] + 2):
        record["status"] = "paused_insufficient_signal_history"
        return record
    closes = [float(item["close"]) for item in bars]
    units = float(record["units"])
    cash = float(record["cash_usd"])
    age = int(record["holding_days"])
    action = foundry.signal(closes, i + 1, spec, units > 0, age)
    opening, closing = float(new["open"]), float(new["close"])
    if action == "BUY" and units == 0 and cash > 0:
        units = cash / (opening * (1 + COST))
        cash = 0.
        age = 0
        record["orders"] += 1
    elif action == "SELL" and units > 0:
        cash = units * opening * (1 - COST)
        units = 0.
        age = 0
        record["orders"] += 1
        record["closed_trades"] += 1
    if units > 0:
        age += 1
    if record.get("hold_units") is None:
        # Frozen benchmark shares acquired only on first FUTURE candle.
        record["hold_units"] = CAPITAL / (opening * (1 + COST))
    marked = cash + units * closing * (1 - COST)
    benchmark = float(record["hold_units"]) * closing * (1 - COST)
    if not all(math.isfinite(x) and x >= 0 for x in (marked, benchmark)):
        raise ValueError("invalid_forward_equity")
    peak = max(marked, float(record["peak_usd"]))
    record.update({
        "last_t": new["t"], "cash_usd": round(cash, 8),
        "units": round(units, 12), "holding_days": age,
        "observed_days": int(record["observed_days"]) + 1,
        "peak_usd": round(peak, 8),
        "max_drawdown_pct": round(max(float(record["max_drawdown_pct"]),
                                    100 * (peak - marked) / peak), 5),
        "value_usd": round(marked, 6),
        "net_pct": round(100 * (marked / CAPITAL - 1), 5),
        "hold_net_pct": round(100 * (benchmark / CAPITAL - 1), 5),
        "excess_vs_hold_points": round(100 * (marked - benchmark) / CAPITAL, 5),
        "status": "observing_paper_only",
    })
    return record


def build(now, knowledge, candles, previous):
    ideas = knowledge.get("ideas", []) if isinstance(knowledge, dict) else []
    if not isinstance(ideas, list):
        ideas = []
    prior = previous.get("tracks", {}) if isinstance(previous, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    tracks = {}
    events = []
    for idea in ideas:
        if len(tracks) >= MAX_TRACKED:
            break
        if not isinstance(idea, dict) or not isinstance(idea.get("spec"), dict):
            continue
        try:
            spec = foundry.normalise(idea["spec"])
        except (ValueError, TypeError):
            continue
        key = foundry.identifier(spec)
        bars = candles.get(spec["asset"]) if isinstance(candles, dict) else None
        try:
            foundry.validate_bars(bars, now)
        except (ValueError, TypeError):
            old = prior.get(key)
            if isinstance(old, dict):
                tracks[key] = dict(old, status="paused_market_data_unavailable")
            continue
        if key in prior and isinstance(prior[key], dict):
            # Ignore stale or tampered state. Never reset and claim past profits.
            rec = dict(prior[key])
            try:
                if rec.get("id") != key or foundry.identifier(foundry.normalise(rec["spec"])) != key:
                    raise ValueError("mismatched_frozen_specification")
                rec = advance(rec, bars)
            except (ValueError, TypeError, KeyError, OverflowError) as error:
                rec["status"] = "paused_invalid_forward_state"
                events.append({"id": key, "status": rec["status"],
                               "reason": type(error).__name__})
        else:
            rec = register(idea, bars, now)
            events.append({"id": key, "status": "forward_paper_registered"})
        tracks[key] = rec
    output = {
        "schema": 1, "generated_at": now.isoformat(),
        "tracked": len(tracks), "robots_modified": False,
        "real_orders": False,
        "trials": [
            {"id": rec["id"], "source": rec.get("source"),
             "asset": rec["spec"]["asset"], "logic": rec["spec"]["logic"],
             "observed_days": rec["observed_days"],
             "closed_trades": rec["closed_trades"], "net_pct": rec.get("net_pct"),
             "excess_vs_hold_points": rec.get("excess_vs_hold_points"),
             "max_drawdown_pct": rec["max_drawdown_pct"], "status": rec["status"],
             "sufficient_evidence": False}
            for rec in tracks.values()
        ],
        "events": events,
        "warning": "Forward paper fills are modeled after daily candle closure, not real executable orders; no profitability proven.",
    }
    state = {"schema": 1, "updated_at": now.isoformat(), "tracks": tracks,
             "real_orders": False}
    return output, state


def main():
    now = datetime.now(timezone.utc)
    result, state = build(now, read(KNOWLEDGE), read(CANDLES), read(STATE))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Strategy forward paper:", result["tracked"], "candidate tracks")


if __name__ == "__main__":
    main()
