"""Free-market pulse: observed price regimes, market context and sampled transfers.

This is descriptive, never a buy/sell signal and not a replacement for a
price-quality-controlled execution feed.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDLES = ROOT / "reports/challenger_candles.json"
CONTEXT = ROOT / "reports/market_context.json"
TRANSFERS = ROOT / "reports/large_transfer_observations.json"
OUTPUT = ROOT / "reports/market_pulse.json"


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def build(now, candles, context, transfers):
    result = {
        "schema": 1, "generated_at": now.isoformat(),
        "kind": "market_context_observations_not_trading_signals",
        "real_orders": False, "signal_count": 0,
        "assets": {}, "macro": {}, "large_transfers": {},
        "issues": {},
        "limitations": [
            "Only closed daily Kraken OHLC; no intraday execution inference.",
            "Sentiment, TVL and stablecoin supply cannot prove future price movement.",
            "Large on-chain transfers are sampled; not an exhaustive whale feed, nor confirmed trades.",
        ],
    }
    for symbol in ("BTCUSD", "ETHUSD", "SOLUSD"):
        raw = candles.get(symbol)
        try:
            if not isinstance(raw, list) or len(raw) < 31:
                raise ValueError("Not enough historical closes")
            closed = [float(x["close"]) for x in raw[-31:]]
            if not all(math.isfinite(x) and x > 0 for x in closed):
                raise ValueError("Invalid closing values")
            timestamp = int(raw[-1]["t"])
            if not 0 < now.timestamp() - timestamp < 5*86400:
                raise ValueError("Stale last daily candle")
            pct = lambda old: round(100 * (closed[-1] / old - 1), 3)
            daily_log_returns = [math.log(closed[i] / closed[i-1]) for i in range(1, len(closed))]
            mean = sum(daily_log_returns) / len(daily_log_returns)
            volatility = math.sqrt(365 * sum((x - mean)**2 for x in daily_log_returns)
                                   / max(1, len(daily_log_returns)-1)) * 100
            result["assets"][symbol] = {
                "last_closed_day_utc": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
                "last_close_usd": round(closed[-1], 4),
                "change_1d_pct": pct(closed[-2]),
                "change_7d_pct": pct(closed[-8]),
                "change_30d_pct": pct(closed[0]),
                "realized_volatility_30d_annualized_pct": round(volatility, 2),
                "direction_7d": "up" if pct(closed[-8]) > 0 else ("down" if pct(closed[-8]) < 0 else "flat"),
                "source": "Kraken closed daily OHLC, research only",
            }
        except (ValueError, TypeError, KeyError, IndexError, OverflowError) as error:
            result["issues"][symbol] = type(error).__name__ + ": " + str(error)[:120]
    if isinstance(context, dict) and context.get("model") == "market_context_observation_v1":
        try:
            age = (now-datetime.fromisoformat(context["generated_at"])).total_seconds()
            if not 0 <= age <= 12*3600: raise ValueError("Market macro stale")
            obs = context.get("observations", {})
            feeling = obs.get("sentiment", {})
            tvl = obs.get("chain_tvl", {}).get("tvl_usd_by_chain", {})
            coins = obs.get("stablecoins", {})
            result["macro"] = {
                "fear_greed_index": feeling.get("index"),
                "tvl_ethereum_usd": tvl.get("Ethereum"),
                "tvl_solana_usd": tvl.get("Solana"),
                "stablecoin_supply_usd_estimate": coins.get("circulating_usd_estimate"),
                "source_errors": context.get("errors", {}),
            }
        except (KeyError, TypeError, ValueError) as error:
            result["issues"]["macro"] = type(error).__name__
    if isinstance(transfers, dict):
        try:
            age = (now-datetime.fromisoformat(transfers["generated_at"])).total_seconds()
            if not 0 <= age <= 12*3600: raise ValueError("Stale whale sample")
            result["large_transfers"] = {
                "state": transfers.get("state"),
                "coverage": transfers.get("coverage"),
                "sampled_records": transfers.get("sampled_records", {}),
                "large_transfers_observed": transfers.get("large_transfers_observed", 0),
                "new_in_sample": len(transfers.get("large_transfers_new", [])),
                "largest_nominal_usd": max(
                    (float(x.get("nominal_usd_approx", 0)) for x in transfers.get("sample_highlights", [])),
                    default=0),
                "source": transfers.get("source"),
                "is_verified_buy_sell": False,
            }
        except (KeyError, TypeError, ValueError) as error:
            result["issues"]["large_transfers"] = type(error).__name__
    return result


def main():
    now = datetime.now(timezone.utc)
    report = build(now, read(CANDLES), read(CONTEXT), read(TRANSFERS))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Market pulse", len(report["assets"]), "assets; whale sample",
          report["large_transfers"].get("state", "absent"))


if __name__ == "__main__":
    main()
