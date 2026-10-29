"""Point-in-time AIT market evidence ledger.

Retain bounded, dated SOURCE observations to let research compare regimes.
This is neither a price oracle nor a predictive classifier. Missing values
stay missing, publisher headlines remain unverified and transfers are not buys.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PULSE = ROOT / "reports/market_pulse.json"
NEWS = ROOT / "reports/market_news.json"
OUTPUT = ROOT / "state/market_feature_history.json"
SUMMARY = ROOT / "reports/market_knowledge.json"
MAX_DAYS = 365
ASSETS = ("BTCUSD", "ETHUSD", "SOLUSD")
METRICS = ("last_close_usd", "change_1d_pct", "change_7d_pct",
           "change_30d_pct", "realized_volatility_30d_annualized_pct")
MACRO = ("fear_greed_index", "tvl_ethereum_usd", "tvl_solana_usd",
         "stablecoin_supply_usd_estimate")
PUBLISHERS = ("Fed", "BCE", "CoinDesk")


def read(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def finite(raw, minimum=None, maximum=None):
    if isinstance(raw, bool):
        return None
    try:
        number = float(raw)
    except (ValueError, TypeError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    if minimum is not None and number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return round(number, 6)


def stamp(value, now, max_age_hours=6):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        seconds = (now - dt).total_seconds()
        return dt if -300 <= seconds <= max_age_hours * 3600 else None
    except (TypeError, ValueError, OverflowError):
        return None


def snapshot(now, pulse, news):
    if (not isinstance(pulse, dict) or pulse.get("schema") != 1
            or pulse.get("real_orders") is not False):
        return None
    observed = stamp(pulse.get("generated_at"), now)
    if not observed:
        return None
    known = pulse.get("assets", {})
    if not isinstance(known, dict):
        return None
    assets = {}
    for asset in ASSETS:
        raw = known.get(asset, {})
        if not isinstance(raw, dict) or "Kraken" not in str(raw.get("source", "")):
            continue
        values = {
            k: finite(raw.get(k), minimum=0) if k == "last_close_usd"
            else finite(raw.get(k), minimum=0, maximum=1000)
                 if k == "realized_volatility_30d_annualized_pct"
            else finite(raw.get(k), minimum=-100, maximum=10000)
            for k in METRICS
        }
        if values["last_close_usd"] is None:
            continue
        assets[asset] = {
            "source": "Kraken closed daily OHLC",
            "last_closed_day": raw.get("last_closed_day_utc"),
            **values,
        }
    if not assets:
        return None
    macro_raw = pulse.get("macro", {})
    macro_raw = macro_raw if isinstance(macro_raw, dict) else {}
    macro = {
        key: finite(macro_raw.get(key), minimum=0, maximum=100)
             if key == "fear_greed_index"
             else finite(macro_raw.get(key), minimum=0)
        for key in MACRO
    }
    whales = pulse.get("large_transfers", {})
    whales = whales if isinstance(whales, dict) else {}
    transfer_sample = {
        "state": whales.get("state") if whales.get("state") in
                 ("observing", "partial", "unavailable") else "unknown",
        "large_transfers_observed": (
            int(whales["large_transfers_observed"])
            if type(whales.get("large_transfers_observed")) is int
            and 0 <= whales["large_transfers_observed"] <= 10000 else None),
        "coverage": str(whales.get("coverage", ""))[:85],
        "not_verified_buy_sell": True,
        "source": "Ethereum public Blockscout transfer sample",
    }
    publisher_count = {name: 0 for name in PUBLISHERS}
    if (isinstance(news, dict) and news.get("schema") == 1
            and news.get("status") in ("available", "partial")
            and stamp(news.get("generated_at"), now)):
        for article in news.get("articles", [])[:20]:
            if isinstance(article, dict) and article.get("source") in PUBLISHERS:
                publisher_count[article["source"]] += 1
    return {
        "date_utc": now.date().isoformat(),
        "observed_at": observed.isoformat(),
        "assets": assets, "macro": macro,
        "transfer_sample": transfer_sample,
        "news_publisher_counts": publisher_count,
        "source_quality": "observed_indicators_not_trading_signals",
        "has_verified_trade_signal": False,
    }


def build(now, pulse, news, previous):
    prior = previous.get("days", []) if isinstance(previous, dict) else []
    prior = prior if isinstance(prior, list) else []
    records = [r for r in prior if isinstance(r, dict)
               and isinstance(r.get("date_utc"), str)
               and r.get("date_utc") <= now.date().isoformat()]
    # Entries are unique per UTC day. Late same-day validated observations win.
    by_date = {r["date_utc"]: r for r in records}
    current = snapshot(now, pulse, news)
    if current:
        key = current["date_utc"]
        old = by_date.get(key, {})
        if not old or str(old.get("observed_at", "")) <= current["observed_at"]:
            by_date[key] = current
    # Never fill missing historical days or mix snapshots across days.
    records = [by_date[key] for key in sorted(by_date)[-MAX_DAYS:]]
    ledger = {
        "schema": 1, "updated_at": now.isoformat(),
        "days": records, "source": "recorded_public_data_only",
        "is_predictive_model": False, "real_orders": False,
    }
    summary = {
        "schema": 1, "generated_at": now.isoformat(),
        "observed_days": len(records),
        "last_observed_at": records[-1]["observed_at"] if records else None,
        "latest": records[-1] if records else None,
        "readiness": "building_point_in_time_history"
                     if len(records) < 30 else "historical_analysis_possible_not_proof",
        "retention": MAX_DAYS, "not_prediction": True,
        "no_real_orders": True, "news_is_unverified": True,
        "wallet_transfers_are_not_trades": True,
    }
    return ledger, summary


def model_memory(ledger):
    days = ledger.get("days", []) if isinstance(ledger, dict) else []
    if not isinstance(days, list):
        days = []
    recent = []
    for item in days[-5:]:
        if not isinstance(item, dict):
            continue
        recent.append({
            "date_utc": str(item.get("date_utc", ""))[:10],
            "assets": {k: {
                "change_7d_pct": v.get("change_7d_pct"),
                "volatility_30d_pct": v.get("realized_volatility_30d_annualized_pct"),
            } for k, v in item.get("assets", {}).items()
              if k in ASSETS and isinstance(v, dict)},
            "sentiment": item.get("macro", {}).get("fear_greed_index"),
        })
    return {
        "total_recorded_days": min(len(days), MAX_DAYS), "recent_regimes": recent,
        "warning": "These are collected observations, not independently verified trading signals.",
    }


def main():
    now = datetime.now(timezone.utc)
    ledger, summary = build(now, read(PULSE), read(NEWS), read(OUTPUT))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Market knowledge:", summary["observed_days"], "distinct UTC dates")


if __name__ == "__main__":
    main()
