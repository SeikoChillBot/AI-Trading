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
CHAMPIONS = ROOT / "reports/strategy_competition.json"
MAX_TRACKED = 24
MAX_ARCHIVED = 120
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


def build(now, knowledge, candles, previous, leaderboard=None):
    ideas = knowledge.get("ideas", []) if isinstance(knowledge, dict) else []
    if not isinstance(ideas, list):
        ideas = []
    prior = previous.get("tracks", {}) if isinstance(previous, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    tracks = {}
    events = []
    # Always admit recently invented strategies. Reserve places for validated
    # paper champions, then rotate out the oldest trials as capacity fills.
    # Archived trials are retained as *terminated paper studies*, not profits.
    qualified = set()
    if (isinstance(leaderboard, dict) and leaderboard.get("schema") == 1
            and leaderboard.get("real_orders") is False
            and leaderboard.get("robots_modified") is False):
        for row in leaderboard.get("ranked", [])[:24]:
            if isinstance(row, dict) and row.get("stage") == "paper_champion":
                qualified.add(row.get("id"))
    preferred = []
    for idea in ideas:
        if not isinstance(idea, dict) or not isinstance(idea.get("spec"), dict):
            continue
        try:
            valid = foundry.normalise(idea["spec"])
            if idea.get("id") != foundry.identifier(valid):
                continue
            preferred.append(idea)
        except (ValueError, TypeError, KeyError):
            continue
    pinned = [item for item in preferred if item["id"] in qualified]
    newest = list(reversed([item for item in preferred if item["id"] not in qualified]))
    selected = (pinned + newest)[:MAX_TRACKED]
    # Iterate in priority order (champions, then most recently created).
    # Restoring original order before the cap can starve new entries.
    for idea in selected:
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
    earlier_archive = previous.get("archived", []) if isinstance(previous, dict) else []
    archive = [x for x in earlier_archive if isinstance(x, dict)][-MAX_ARCHIVED:]
    for key, old in prior.items():
        if key not in tracks and isinstance(old, dict) and not any(
                x.get("id") == key for x in archive):
            archive.append({
                "id": key, "source": old.get("source"),
                "last_t": old.get("last_t"), "observed_days": old.get("observed_days", 0),
                "net_pct": old.get("net_pct"), "status": "archived_capacity_rotation",
                "archived_at": now.isoformat(),
            })
            events.append({"id": key, "status": "archived_capacity_rotation"})
    archive = archive[-MAX_ARCHIVED:]
    output = {
        "schema": 1, "generated_at": now.isoformat(),
        "tracked": len(tracks), "archived_trials": len(archive),
        "robots_modified": False,
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
             "archived": archive, "real_orders": False}
    return output, state


def main():
    now = datetime.now(timezone.utc)
    result, state = build(now, read(KNOWLEDGE), read(CANDLES), read(STATE), read(CHAMPIONS))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Strategy forward paper:", result["tracked"], "candidate tracks")


if __name__ == "__main__":
    main()
