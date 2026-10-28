"""Forward-only paper challenger incubator from fixed, tested parameter grid.

Candidate definitions are selected by a deterministic historical walk-forward
module, NEVER by executing model-written code. Each starts only AFTER its
creation date. It is independent of the original 36 paper robots.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from research import walkforward as wf

ROOT = Path(__file__).resolve().parents[1]
CANDLES = ROOT / "reports/challenger_candles.json"
RESEARCH = ROOT / "reports/challenger_walkforward.json"
STATE = ROOT / "state/challenger_incubator.json"
REPORT = ROOT / "reports/challenger_incubator.json"
HISTORY = ROOT / "reports/challenger_incubator_history.jsonl"
CAPITAL = 20.0
ALLOWED = {(x["window"], x["buffer"]) for x in wf.PARAMS}


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def seed(asset, params, last, now, version=1):
    if (params.get("window"), params.get("buffer")) not in ALLOWED:
        raise ValueError("Candidate not from the approved grid")
    return {
        "asset": asset, "version": version,
        "parameters": {"window": params["window"], "buffer": params["buffer"]},
        "created_at": now.isoformat(), "last_processed_t": int(last),
        "cash": CAPITAL, "units": 0.0, "fees": 0.0, "orders": 0,
        "closed_trades": 0, "peak": CAPITAL, "worst_drawdown_pct": 0.0,
        "hold_units": None, "hold_equity": CAPITAL,
        "observation_count": 0, "status": "prospective_waiting_next_closed_candle",
        "eligible_for_real_trading": False, "profit_proven": False,
    }


def step(item, bars, now):
    """Never replay the seed candle; model next-open fills with fees and slippage."""
    if (item["parameters"]["window"], item["parameters"]["buffer"]) not in ALLOWED:
        raise ValueError("Mutated or unsupported parameters")
    last = item["last_processed_t"]
    ix = next((i for i, bar in enumerate(bars) if bar["t"] == last), None)
    if ix is None:
        raise ValueError("Missing last observed market candle; no guessed continuity")
    future = bars[ix+1:]
    if not future:
        return item, []
    if len(future) > 1:
        # No reconstructing a missed period as if it had been observed live.
        raise ValueError("Observation gap; retire and reseed independently")
    index = ix+1
    bar = bars[index]
    opening = wf.number(bar["open"])
    closing = wf.number(bar["close"])
    action = wf.signal(bars, index, item["parameters"], item["units"] > 0)
    cost = wf.COST
    if item["hold_units"] is None:
        item["hold_units"] = CAPITAL/(opening*(1+cost))
    if action == "BUY" and item["units"] == 0:
        item["fees"] += item["cash"]*cost/(1+cost)
        item["units"] = item["cash"]/(opening*(1+cost))
        item["cash"] = 0.0
        item["orders"] += 1
    elif action == "SELL" and item["units"] > 0:
        gross = item["units"]*opening
        item["fees"] += gross*cost
        item["cash"] = gross*(1-cost)
        item["units"] = 0.0
        item["orders"] += 1
        item["closed_trades"] += 1
    equity = item["cash"]+item["units"]*closing*(1-cost)
    if not math.isfinite(equity) or equity < 0:
        raise ValueError("Invalid paper equity")
    item["peak"] = max(item["peak"], equity)
    item["worst_drawdown_pct"] = max(item["worst_drawdown_pct"],
                                     100*(item["peak"]-equity)/item["peak"])
    item["hold_equity"] = item["hold_units"]*closing*(1-cost)
    item["last_processed_t"] = int(bar["t"])
    item["observation_count"] += 1
    item["status"] = "forward_paper_observing"
    row = {
        "asset": item["asset"], "version": item["version"],
        "candle_t": item["last_processed_t"], "signal_from_previous_close": action,
        "equity_usd": round(equity, 6), "hold_usd": round(item["hold_equity"], 6),
        "orders_total": item["orders"], "closed_roundtrips_total": item["closed_trades"],
        "fee_model_per_side": cost,
        "test_type": "forward_only_candle_after_candidate_registration",
        "real_order": False,
    }
    return item, [row]


def build(now, candles, research, state):
    existing = state.get("active", {}) if isinstance(state, dict) else {}
    retired = state.get("retired", []) if isinstance(state, dict) else []
    if not isinstance(existing, dict) or not isinstance(retired, list):
        raise ValueError("Invalid registry")
    output = {
        "schema": 1, "generated_at": now.isoformat(),
        "model": "frozen_forward_paper_challengers_v1",
        "starting_capital_per_candidate_usd": CAPITAL,
        "assets": {}, "errors": {}, "new_history": [],
        "historical_bot_portfolios_untouched": True,
        "gemini_code_execution": False, "real_orders": False,
        "automatic_promotion": False,
        "warning": "Prospective paper-only results; fixed parameters chosen with previously reused historical data. Not proof of future returns.",
    }
    if research.get("model") != "kraken_daily_walkforward_v1":
        return output, {"schema": 1, "active": existing, "retired": retired}
    for asset in wf.PAIRS:
        candidate = research.get("instruments", {}).get(asset, {})
        bars = candles.get(asset)
        if not isinstance(bars, list) or not isinstance(candidate, dict):
            output["errors"][asset] = "No validated daily market history"
            continue
        try:
            wf.validate(bars, now)
            fresh = dict(existing.get(asset, {}))
            if not fresh:
                fresh = seed(asset, candidate["candidate_parameters"], bars[-1]["t"], now)
            else:
                try:
                    fresh, rows = step(fresh, bars, now)
                    output["new_history"].extend(rows)
                except ValueError as exc:
                    if "Observation gap" not in str(exc):
                        raise
                    # Retire rather than pretend missed data had been observed live.
                    retired.append({
                        "asset": asset, "version": fresh["version"],
                        "retired_at": now.isoformat(), "reason": "unobserved_market_gap",
                        "last_processed_t": fresh["last_processed_t"],
                        "observations": fresh["observation_count"],
                    })
                    fresh = seed(asset, candidate["candidate_parameters"], bars[-1]["t"],
                                 now, fresh["version"]+1)
            existing[asset] = fresh
            equity = fresh["cash"]+fresh["units"]*bars[-1]["close"]*(1-wf.COST)
            output["assets"][asset] = {
                "version": fresh["version"], "created_at": fresh["created_at"],
                "status": fresh["status"], "parameters": fresh["parameters"],
                "last_observation_t": fresh["last_processed_t"],
                "observations": fresh["observation_count"],
                "equity_usd": round(equity, 5),
                "net_return_pct": round(100*(equity/CAPITAL-1), 4),
                "hold_equity_usd": round(fresh["hold_equity"], 5),
                "worst_drawdown_pct": round(fresh["worst_drawdown_pct"], 4),
                "closed_trades": fresh["closed_trades"],
                "orders": fresh["orders"], "fees_paid_estimate_usd": round(fresh["fees"], 5),
                "ready_for_review": (fresh["observation_count"] >= 60
                                     and fresh["closed_trades"] >= 20),
                "auto_modify_original_robots": False,
            }
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            output["errors"][asset] = type(exc).__name__ + ": " + str(exc)[:140]
    return output, {"schema":1, "active":existing, "retired":retired[-30:]}


def main():
    now = datetime.now(timezone.utc)
    output, state = build(now, read(CANDLES), read(RESEARCH), read(STATE))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({k:v for k,v in output.items() if k!="new_history"},
                                 ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if output["new_history"]:
        with HISTORY.open("a", encoding="utf-8") as stream:
            for row in output["new_history"]:
                stream.write(json.dumps(row, ensure_ascii=False)+"\n")
    print("Incubator: %d forward-only paper challengers, %d new candles, %d source issues"
          % (len(output["assets"]), len(output["new_history"]), len(output["errors"])))


if __name__ == "__main__":
    main()
