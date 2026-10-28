"""Educational paper trading only. No exchange orders or API keys."""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import requests

STATE = Path("state/portfolios.json")
REPORT = Path("reports/latest.csv")
FEE = 0.001
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
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
]

def fetch_candles(symbol):
    pair = {"BTCUSDT": "XBTUSD", "ETHUSDT": "ETHUSD", "SOLUSDT": "SOLUSD"}[symbol]
    response = requests.get(
        "https://api.kraken.com/0/public/OHLC",
        params={"pair": pair, "interval": 15},
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

def decide(mode, prices, holding):
    last = prices[-1]
    mean20 = sum(prices[-20:]) / 20
    if mode == "hold":
        return "buy" if not holding else "wait"
    if mode == "momentum":
        return ("buy" if last > mean20 * 1.003 else "sell") if not holding else ("sell" if last < mean20 * 0.997 else "wait")
    if mode == "reversion":
        return ("buy" if last < mean20 * 0.99 else "wait") if not holding else ("sell" if last > mean20 * 1.005 else "wait")
    if mode == "breakout":
        return ("buy" if last > max(prices[-21:-1]) else "wait") if not holding else ("sell" if last < min(prices[-11:-1]) else "wait")
    return "wait"

def main():
    market = {symbol: fetch_candles(symbol) for symbol in SYMBOLS}
    now = datetime.now(timezone.utc).isoformat()
    state = json.loads(STATE.read_text()) if STATE.exists() else {"created": now, "portfolios": {}, "last_candle": {}}
    portfolios = state["portfolios"]
    rows = []
    for name, symbol, mode in STRATEGIES:
        candles = market[symbol]
        timestamp, price = candles[-1]
        portfolio = portfolios.setdefault(name, {"cash": 20.0, "units": 0.0, "trades": 0, "fees": 0.0})
        if state["last_candle"].get(name) != timestamp:
            action = decide(mode, [p for _, p in candles], portfolio["units"] > 0)
            if action == "buy" and portfolio["cash"] > 0:
                gross = portfolio["cash"]
                portfolio["units"] += gross * (1 - FEE) / price
                portfolio["fees"] += gross * FEE
                portfolio["cash"] = 0.0
                portfolio["trades"] += 1
            elif action == "sell" and portfolio["units"] > 0:
                gross = portfolio["units"] * price
                portfolio["cash"] += gross * (1 - FEE)
                portfolio["fees"] += gross * FEE
                portfolio["units"] = 0.0
                portfolio["trades"] += 1
            state["last_candle"][name] = timestamp
        equity = portfolio["cash"] + portfolio["units"] * price
        rows.append({"strategy": name, "asset": symbol, "capital_usd": round(equity, 5),
                     "return_pct": round((equity / 20 - 1) * 100, 3), "trades": portfolio["trades"],
                     "fees_usd": round(portfolio["fees"], 5), "candle_end_ms": timestamp})
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
