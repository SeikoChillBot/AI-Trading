"""Educational paper trading only. No exchange orders or API keys."""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import requests
from research.robot_tuning import active_scales, scale_for

STATE = Path("state/portfolios.json")
REPORT = Path("reports/latest.csv")
FEE = 0.001
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
TIMEFRAMES = {
    "btc_hold": 60, "eth_hold": 60, "sol_hold": 60,
    "btc_momentum": 5, "eth_momentum": 15, "sol_momentum": 5,
    "btc_reversion": 5, "eth_reversion": 15, "sol_reversion": 5,
    "btc_breakout": 15, "btc_rsi": 5, "eth_ema_cross": 15,
    "sol_bollinger": 5, "btc_volatility": 60,
    "btc_scalp_momentum": 5, "eth_scalp_trailing": 5,
    "sol_scalp_microtrend": 5, "btc_scalp_conservative": 5,
}
STRATEGIES = [
    ("btc_hold", "BTCUSDT", "hold"),
    ("eth_hold", "ETHUSDT", "hold"),
    ("sol_hold", "SOLUSDT", "hold"),
    ("btc_momentum", "BTCUSDT", "momentum"),
    ("eth_momentum", "ETHUSDT", "momentum"),
    ("sol_momentum", "SOLUSDT", "momentum"),
    ("btc_reversion", "BTCUSDT", "reversion"),
    ("eth_reversion", "ETHUSDT", "reversion"),
    ("sol_reversion", "SOLUSDT", "reversion"),
    ("btc_breakout", "BTCUSDT", "breakout"),
    ("btc_rsi", "BTCUSDT", "rsi"),
    ("eth_ema_cross", "ETHUSDT", "ema_cross"),
    ("sol_bollinger", "SOLUSDT", "bollinger"),
    ("btc_volatility", "BTCUSDT", "volatility"),
    ("btc_scalp_momentum", "BTCUSDT", "scalp_momentum"),
    ("eth_scalp_trailing", "ETHUSDT", "scalp_trailing"),
    ("sol_scalp_microtrend", "SOLUSDT", "scalp_microtrend"),
    ("btc_scalp_conservative", "BTCUSDT", "scalp_conservative"),
]

def fetch_candles(symbol, interval):
    pair = {"BTCUSDT": "XBTUSD", "ETHUSDT": "ETHUSD", "SOLUSDT": "SOLUSD"}[symbol]
    response = requests.get(
        "https://api.kraken.com/0/public/OHLC",
        params={"pair": pair, "interval": interval},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise ValueError("Kraken API: " + str(payload["error"]))
    result = payload["result"]
    key = next(k for k in result if k != "last")
    candles = result[key]
    if len(candles) < 30:
        raise ValueError("Insufficient candle data for " + symbol)
    # Kraken timestamps denote candle opening; final candle is still forming.
    return [(int(c[0]) * 1000, float(c[4])) for c in candles[:-1]]

def ema(values, period):
    alpha = 2 / (period + 1)
    out = values[0]
    for value in values[1:]:
        out = alpha * value + (1 - alpha) * out
    return out

def rsi(values, period=14):
    diffs = [b-a for a,b in zip(values[-period-1:-1], values[-period:])]
    gains = sum(max(0, d) for d in diffs) / period
    losses = sum(max(0, -d) for d in diffs) / period
    if losses == 0:
        return 100.0 if gains else 50.0
    return 100 - 100 / (1 + gains / losses)

def decide(mode, prices, holding, portfolio=None, threshold_scale=1.0):
    if type(threshold_scale) not in (int, float) or threshold_scale not in (0.8, 1.0, 1.2):
        raise ValueError("Unapproved strategy tuning scale")
    last = prices[-1]
    mean20 = sum(prices[-20:]) / 20
    if mode.startswith("scalp_"):
        portfolio = portfolio or {}
        # Trailing stops are evaluated on CLOSED candles only; gaps may exceed thresholds.
        if holding:
            peak = max(float(portfolio.get("peak_price", last)), last)
            portfolio["peak_price"] = peak
            trail = {"scalp_momentum": .004, "scalp_trailing": .006,
                     "scalp_microtrend": .005, "scalp_conservative": .008}[mode]
            if last <= peak * (1 - trail):
                return "sell"
            if mode == "scalp_microtrend" and last < mean20 * .998:
                return "sell"
            return "wait"
        # Thresholds deliberately exceed the 0.2% modeled round-trip fees.
        rise = last / prices[-4] - 1
        if mode == "scalp_momentum":
            return "buy" if rise > .004*threshold_scale and last > mean20 * (1+.002*threshold_scale) else "wait"
        if mode == "scalp_trailing":
            return "buy" if rise > .005*threshold_scale and last > mean20 * (1+.002*threshold_scale) else "wait"
        if mode == "scalp_microtrend":
            return "buy" if last > mean20 * (1+.003*threshold_scale) and prices[-1] > prices[-2] > prices[-3] else "wait"
        if mode == "scalp_conservative":
            return "buy" if rise > .008*threshold_scale and last > mean20 * (1+.005*threshold_scale) else "wait"
    if mode == "hold":
        return "buy" if not holding else "wait"
    if mode == "momentum":
        return ("buy" if last > mean20 * (1+.003*threshold_scale) else "sell") if not holding else ("sell" if last < mean20 * 0.997 else "wait")
    if mode == "reversion":
        return ("buy" if last < mean20 * (1-.01*threshold_scale) else "wait") if not holding else ("sell" if last > mean20 * 1.005 else "wait")
    if mode == "breakout":
        return ("buy" if last > max(prices[-21:-1]) * (1+.001*(threshold_scale-1)) else "wait") if not holding else ("sell" if last < min(prices[-11:-1]) else "wait")
    if mode == "rsi":
        level = rsi(prices)
        return ("sell" if level > 60 else "wait") if holding else ("buy" if level < 35-8*(threshold_scale-1) else "wait")
    if mode == "ema_cross":
        fast, slow = ema(prices[-60:], 9), ema(prices[-60:], 21)
        return ("sell" if fast < slow else "wait") if holding else ("buy" if fast > slow * (1+.001*threshold_scale) else "wait")
    if mode == "bollinger":
        variance = sum((p - mean20)**2 for p in prices[-20:]) / 20
        std = variance**0.5
        return ("sell" if last > mean20 else "wait") if holding else ("buy" if last < mean20 - (2*threshold_scale)*std else "wait")
    if mode == "volatility":
        high = max(prices[-21:-1]); low = min(prices[-21:-1])
        return ("sell" if last < mean20 else "wait") if holding else ("buy" if last > high*(1+.001*(threshold_scale-1)) and (high-low)/mean20 > .01*threshold_scale else "wait")
    return "wait"

def main():
    market = {(symbol, interval): fetch_candles(symbol, interval)
              for symbol, interval in {(symbol, TIMEFRAMES[name]) for name, symbol, _ in STRATEGIES}}
    now = datetime.now(timezone.utc).isoformat()
    state = json.loads(STATE.read_text()) if STATE.exists() else {"created": now, "portfolios": {}, "last_candle": {}}
    portfolios = state["portfolios"]
    rows = []
    tuning = active_scales()
    for name, symbol, mode in STRATEGIES:
        interval = TIMEFRAMES[name]
        candles = market[(symbol, interval)]
        timestamp, price = candles[-1]
        portfolio = portfolios.setdefault(name, {"cash": 20.0, "units": 0.0, "trades": 0, "fees": 0.0})
        if state["last_candle"].get(name) != timestamp:
            action = decide(mode, [p for _, p in candles], portfolio["units"] > 0, portfolio, scale_for(name, tuning))
            if action == "buy" and portfolio["cash"] > 0:
                gross = portfolio["cash"]
                portfolio["units"] += gross * (1 - FEE) / price
                portfolio["fees"] += gross * FEE
                portfolio["cash"] = 0.0
                portfolio["trades"] += 1
                if mode.startswith("scalp_"):
                    portfolio["peak_price"] = price
            elif action == "sell" and portfolio["units"] > 0:
                gross = portfolio["units"] * price
                portfolio["cash"] += gross * (1 - FEE)
                portfolio["fees"] += gross * FEE
                portfolio["units"] = 0.0
                portfolio["trades"] += 1
                portfolio.pop("peak_price", None)
            state["last_candle"][name] = timestamp
        equity = portfolio["cash"] + portfolio["units"] * price
        rows.append({"strategy": name, "asset": symbol, "capital_usd": round(equity, 5),
                     "return_pct": round((equity / 20 - 1) * 100, 3), "trades": portfolio["trades"],
                     "fees_usd": round(portfolio["fees"], 5), "candle_end_ms": timestamp,
                     "timeframe_min": interval})
    # USD quotes are used. The starting 20 units are USD fictifs, not EUR.
    state["updated"] = now
    STATE.parent.mkdir(exist_ok=True)
    REPORT.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    with REPORT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)

if __name__ == "__main__":
    main()
