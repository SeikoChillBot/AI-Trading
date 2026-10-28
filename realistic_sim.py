"""Forward-only, conservative Kraken spot paper trading. Never submits an order.

Independent from legacy bot.py and its portfolios. No exchange credentials.
Signals use closed OHLC candles; possible fills use a subsequently fetched order book.
"""
import csv
import json
import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

import requests
from bot import STRATEGIES, TIMEFRAMES, fetch_candles, decide, rsi, ema

ROOT = Path(".")
STATE = ROOT / "state/realistic_portfolios.json"
LATEST = ROOT / "reports/realistic_latest.csv"
HISTORY = ROOT / "reports/realistic_history.csv"
ORDERS = ROOT / "reports/realistic_orders.csv"
PAIRS = {"BTCUSDT": "XBTUSD", "ETHUSDT": "ETHUSD", "SOLUSDT": "SOLUSD"}
START_CASH = 20.0
# Kraken Pro level 1, spot market/taker, October 2026.
TAKER_FEE = 0.008
# Additional conservative execution uncertainty, on top of the actual book spread.
SLIPPAGE = 0.0005
MIN_USD = 0.5
MAX_SPREAD = 0.025
MIN_CANDLE_POINTS = 30

LATEST_FIELDS = ["strategy", "asset", "capital_usd", "return_pct",
                 "trades", "fees_usd", "candle_end_ms", "timeframe_min",
                 "cash_usd", "units", "position", "estimated_liquidation_usd"]
HISTORY_FIELDS = ["recorded_at", *LATEST_FIELDS]
ORDER_FIELDS = ["event_id", "observed_at", "strategy", "asset", "side", "status",
                "signal_candle_closed_at", "signal_close", "reason", "reference_price",
                "executed_price", "quantity", "gross_usd", "fee_usd", "net_usd",
                "min_base", "min_cost_usd", "available_cash_usd", "spread_pct"]


def public(endpoint, params):
    response = requests.get("https://api.kraken.com/0/public/" + endpoint,
                            params=params, timeout=20, headers={"User-Agent": "SeikoPaperTrading/2.0"})
    response.raise_for_status()
    body = response.json()
    if body.get("error"):
        raise RuntimeError("Kraken " + str(body["error"]))
    result = body.get("result")
    if not isinstance(result, dict) or not result:
        raise ValueError("Missing Kraken result for " + endpoint)
    return result


def pair_metadata():
    rules = {}
    for symbol, pair in PAIRS.items():
        data = public("AssetPairs", {"pair": pair})
        entries = [v for v in data.values()
                   if isinstance(v, dict) and (v.get("altname") == pair or
                   str(v.get("wsname", "")).replace("/", "") == pair)]
        if len(entries) != 1:
            raise ValueError("Cannot uniquely resolve Kraken spot pair " + pair)
        v = entries[0]
        if "ordermin" not in v or "lot_decimals" not in v:
            raise ValueError("Kraken pair minimum or lot precision missing for " + pair)
        min_base = float(v["ordermin"])
        decimals = int(v["lot_decimals"])
        min_cost = max(MIN_USD, float(v.get("costmin") or MIN_USD))
        if not (0 < min_base < 100000 and 0 <= decimals <= 12 and min_cost > 0):
            raise ValueError("Invalid trading limits for " + pair)
        rules[symbol] = {"min_base": min_base, "lot_decimals": decimals,
                         "min_cost_usd": min_cost, "pair": pair}
    return rules


def orderbook(symbol):
    data = public("Depth", {"pair": PAIRS[symbol], "count": 25})
    book = next(iter(data.values()))
    bids = [(float(v[0]), float(v[1])) for v in book["bids"]]
    asks = [(float(v[0]), float(v[1])) for v in book["asks"]]
    if not bids or not asks or any(p <= 0 or q <= 0 for p,q in bids+asks):
        raise ValueError("Empty or corrupt book for " + symbol)
    if bids[0][0] >= asks[0][0]:
        raise ValueError("Crossed book for " + symbol)
    if any(bids[i][0] < bids[i+1][0] for i in range(len(bids)-1)):
        raise ValueError("Unsorted bids for " + symbol)
    if any(asks[i][0] > asks[i+1][0] for i in range(len(asks)-1)):
        raise ValueError("Unsorted asks for " + symbol)
    spread = (asks[0][0] - bids[0][0]) / ((asks[0][0] + bids[0][0])/2)
    if spread > MAX_SPREAD:
        raise ValueError("Excessive spread, fail closed for " + symbol)
    return {"bids": bids, "asks": asks, "spread_pct": spread*100}


def rounded_quantity(units, decimals):
    quantum = Decimal("1").scaleb(-decimals)
    return float(Decimal(str(units)).quantize(quantum, rounding=ROUND_DOWN))


def executable_buy(cash, book, limits):
    """Walk available asks; fee is reserved from cash; round down base units."""
    budget = cash / (1 + TAKER_FEE)
    remaining = budget
    raw_units = 0.0
    for price, available_units in book["asks"]:
        price *= (1 + SLIPPAGE)
        filled = min(available_units, remaining / price)
        raw_units += filled
        remaining -= filled * price
        if remaining <= 1e-8:
            break
    if remaining > 0.00001:
        return None, "DEPTH_INSUFFICIENT"
    units = rounded_quantity(raw_units, limits["lot_decimals"])
    if units < limits["min_base"]:
        return None, "MINIMUM_VOLUME"
    remaining_units = units
    gross = 0.0
    for price, available_units in book["asks"]:
        filled = min(available_units, remaining_units)
        gross += filled * price * (1 + SLIPPAGE)
        remaining_units -= filled
        if remaining_units <= 1e-12:
            break
    if remaining_units > 1e-9:
        return None, "DEPTH_INSUFFICIENT"
    if gross < limits["min_cost_usd"]:
        return None, "MINIMUM_COST"
    fee = gross * TAKER_FEE
    if gross + fee > cash + 1e-7:
        return None, "INSUFFICIENT_FUNDS"
    return {"units": units, "gross": gross, "fee": fee,
            "price": gross/units, "net": -(gross+fee)}, None


def executable_sell(units, book, limits):
    """Walk available bids, observing base/quote exchange minimums."""
    if units < limits["min_base"]:
        return None, "MINIMUM_VOLUME"
    remaining = units
    gross = 0.0
    for price, available in book["bids"]:
        filled = min(remaining, available)
        gross += filled * price * (1 - SLIPPAGE)
        remaining -= filled
        if remaining <= 1e-12:
            break
    if remaining > 1e-9:
        return None, "DEPTH_INSUFFICIENT"
    if gross < limits["min_cost_usd"]:
        return None, "MINIMUM_COST"
    fee = gross * TAKER_FEE
    return {"units": units, "gross": gross, "fee": fee,
            "price": gross/units, "net": gross-fee}, None


def estimated_liquidation(portfolio, book):
    """Account value if current holdings could be sold at bid, including fees."""
    units = float(portfolio["units"])
    if units <= 0:
        return float(portfolio["cash"])
    # Mark to available bid depth; always conservative on the displayed value.
    remaining = units
    proceeds = 0.0
    for price, volume in book["bids"]:
        filled = min(remaining, volume)
        proceeds += filled * price * (1 - SLIPPAGE) * (1 - TAKER_FEE)
        remaining -= filled
        if remaining <= 1e-12:
            break
    if remaining > 1e-9:
        return None
    return float(portfolio["cash"]) + proceeds


def describe_signal(mode, prices, portfolio, action):
    last=prices[-1]; mean=sum(prices[-20:])/20
    reason = {
        "hold": "Achat unique de conservation",
        "momentum": "Tendance par rapport a la moyenne 20 bougies (seuil 0,3 %)",
        "reversion": "Retour a la moyenne 20 bougies (seuil achat -1 %, vente +0,5 %)",
        "breakout": "Cassure du plus haut 20 bougies ou du plus bas 10 bougies",
        "rsi": "RSI 14 : achat sous 35, vente au-dessus de 60",
        "ema_cross": "Croisement EMA 9 et 21",
        "bollinger": "Bandes de Bollinger (20 bougies, deux ecarts types)",
        "volatility": "Cassure haussiere avec amplitude superieure a 1 %",
        "scalp_momentum": "Scalping momentum 5 min et sortie trailing 0,4 %",
        "scalp_trailing": "Scalping ETH et sortie trailing 0,6 %",
        "scalp_microtrend": "Trois clotures croissantes et sortie trailing 0,5 %",
        "scalp_conservative": "Entree selective +0,8 % et sortie trailing 0,8 %",
    }.get(mode, "Signal non categorise")
    metric = "RSI14=%.1f" % rsi(prices) if mode=="rsi" else "moy20=%.5f" % mean
    return ("%s | signal=%s; close=%.5f; %s" % (reason,action,last,metric))


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    # Download and validate ALL market inputs first. Failure leaves all prior
    # simulated balances untouched and the workflow fails instead of inventing prices.
    market = {(symbol, interval): fetch_candles(symbol, interval)
              for symbol, interval in {(symbol,TIMEFRAMES[name])
                                        for name,symbol,_ in STRATEGIES}}
    rules = pair_metadata()
    books = {symbol: orderbook(symbol) for symbol in PAIRS}
    now = datetime.now(timezone.utc).isoformat()
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
        if state.get("version") != 2:
            raise ValueError("Wrong realistic simulation state version")
    else:
        state = {"version": 2, "created": now, "fee_rate": TAKER_FEE,
                 "slippage_rate": SLIPPAGE, "portfolios": {}, "last_candle": {}}
    portfolios = state["portfolios"]
    rows = []
    events = []
    for name, symbol, mode in STRATEGIES:
        interval = TIMEFRAMES[name]
        candles = market[(symbol, interval)]
        signal_open_ms, price = candles[-1]
        signal_closed_ms = signal_open_ms + interval*60*1000
        holding = portfolios.get(name, {}).get("units", 0) > 0
        portfolio = portfolios.setdefault(name, {"cash": START_CASH, "units": 0.0,
                                                   "trades": 0, "fees": 0.0})
        if int(state["last_candle"].get(name, 0)) != signal_open_ms:
            action = decide(mode, [v for _,v in candles], holding, portfolio)
            if action in ("buy","sell"):
                reason = describe_signal(mode,[v for _,v in candles], portfolio, action)
                book=books[symbol];limits=rules[symbol]
                side=action.upper()
                event={"event_id": now+"-"+name+"-"+action,
                       "observed_at":now,"strategy":name,"asset":symbol,"side":side,
                       "status":"REJECTED","signal_candle_closed_at":
                           datetime.fromtimestamp(signal_closed_ms/1000,timezone.utc).isoformat(),
                       "signal_close":round(price,8),"reason":reason,
                       "reference_price":book["asks"][0][0] if action=="buy" else book["bids"][0][0],
                       "executed_price":"","quantity":"","gross_usd":"","fee_usd":"",
                       "net_usd":"","min_base":limits["min_base"],
                       "min_cost_usd":limits["min_cost_usd"],"available_cash_usd":
                       round(portfolio["cash"],8),"spread_pct":round(book["spread_pct"],5)}
                if action=="buy" and portfolio["cash"]>0:
                    fill, reject = executable_buy(portfolio["cash"],book,limits)
                elif action=="sell" and portfolio["units"]>0:
                    fill, reject = executable_sell(portfolio["units"],book,limits)
                else:
                    fill,reject = None,"NO_BALANCE"
                if fill is not None:
                    if action=="buy":
                        portfolio["cash"] = max(0.0, portfolio["cash"] + fill["net"])
                        portfolio["units"] += fill["units"]
                        if mode.startswith("scalp_"):
                            portfolio["peak_price"] = price
                    else:
                        portfolio["cash"] += fill["net"]
                        portfolio["units"] = 0.0
                        portfolio.pop("peak_price",None)
                    portfolio["trades"] += 1
                    portfolio["fees"] += fill["fee"]
                    event.update(status="FILLED_SIMULATED",executed_price=round(fill["price"],8),
                                 quantity=fill["units"],gross_usd=round(fill["gross"],8),
                                 fee_usd=round(fill["fee"],8),net_usd=round(fill["net"],8))
                else:
                    event["status"] = reject
                    event["reason"] += " | refusal="+reject
                events.append(event)
            state["last_candle"][name] = signal_open_ms
        equity = estimated_liquidation(portfolio,books[symbol])
        if equity is None:
            raise ValueError("Insufficient current book depth to value position "+name)
        rows.append({"strategy":name,"asset":symbol,
                     "capital_usd":round(equity,5),
                     "return_pct":round((equity/START_CASH-1)*100,3),
                     "trades":portfolio["trades"],
                     "fees_usd":round(portfolio["fees"],5),
                     "candle_end_ms":signal_closed_ms,
                     "timeframe_min":interval,
                     "cash_usd":round(portfolio["cash"],8),
                     "units":round(portfolio["units"],12),
                     "position":"CRYPTO" if portfolio["units"]>0 else "USD",
                     "estimated_liquidation_usd":round(equity,5)})
    # One batch is one self-contained snapshot: preserve historical rows, add
    # exact observed_at to avoid confusing candle times with execution times.
    new_history=read_csv(HISTORY)
    new_history.extend({"recorded_at":now,**row} for row in rows)
    new_orders=read_csv(ORDERS)
    new_orders.extend(events)
    state["updated"]=now
    state["last_book_observed_at"]=now
    state["market_assumptions"]={"maker_fee_not_used":True,
                                 "taker_fee_pct":TAKER_FEE*100,
                                 "extra_slippage_pct":SLIPPAGE*100,
                                 "quotes":"Kraken public order book",
                                 "mark":"estimated liquidation proceeds after taker fee"}
    STATE.parent.mkdir(parents=True,exist_ok=True)
    write_csv(LATEST,rows,LATEST_FIELDS)
    write_csv(HISTORY,new_history,HISTORY_FIELDS)
    write_csv(ORDERS,new_orders,ORDER_FIELDS)
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Realistic paper trading: 18 strategies, new events",len(events),
          "capital",round(sum(float(r["capital_usd"]) for r in rows),3),
          "fee",TAKER_FEE,"slippage",SLIPPAGE,"UTC",now)


if __name__=="__main__":
    main()
