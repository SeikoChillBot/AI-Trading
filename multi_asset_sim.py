"""Seiko Multi-Market Lab — forward-only indicative paper simulation.

Stocks/ETFs use observed public US market quotes (Yahoo chart, unofficial/delayed).
EUR/USD uses ECB information-only daily reference rates, NOT executable FX quotes.
No broker/API keys, no live orders, no shorting, no leverage, no invented prices.
Crypto V2 remains entirely separate.
"""
import csv
import json
import math
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

STATE = Path("state/multi_asset_portfolios.json")
LATEST = Path("reports/multi_asset_latest.csv")
HISTORY = Path("reports/multi_asset_history.csv")
EVENTS = Path("reports/multi_asset_orders.csv")
STATUS = Path("reports/multi_asset_sources.json")
CACHE = Path("reports/multi_asset_quotes_cache.json")
FX_CACHE = Path("reports/fx_reference.json")
START = 1000.0
FEE_RATE = 0.001  # illustrative broker fee, NOT a published broker price
MIN_FEE = 1.0
HALF_SPREAD = 0.0005  # indicative cost per side; real spread not captured
SLIP = 0.001  # additional conservative per-side price uncertainty
FX_FEE = 0.0015
FX_HALF_SPREAD = 0.001
FX_SLIP = 0.001
MARKET_TZ = ZoneInfo("America/New_York")
PAIR_TZ = ZoneInfo("Europe/Paris")
SPECS = [
    ("AAPL", "Apple", "actions", "US equity", "Yahoo Finance (unofficial)"),
    ("MSFT", "Microsoft", "actions", "US equity", "Yahoo Finance (unofficial)"),
    ("SPY", "SPDR S&P 500 ETF", "etf", "US ETF proxy (not EU UCITS)", "Yahoo Finance (unofficial)"),
    ("QQQ", "Invesco QQQ", "etf", "US ETF proxy (not EU UCITS)", "Yahoo Finance (unofficial)"),
    ("BND", "Vanguard Total Bond Market ETF", "obligations", "US bond ETF proxy", "Yahoo Finance (unofficial)"),
    ("GLD", "SPDR Gold Shares", "or", "US gold-linked ETF proxy", "Yahoo Finance (unofficial)"),
    ("SLV", "iShares Silver Trust", "argent", "US silver-linked ETF proxy", "Yahoo Finance (unofficial)"),
    ("VNQ", "Vanguard Real Estate ETF", "immobilier", "US REIT ETF proxy", "Yahoo Finance (unofficial)"),
    ("EURUSD", "EUR/USD (référence BCE)", "forex", "ECB reference, not tradable", "European Central Bank"),
]
RULES = {"hold": "Conserver après une première entrée éligible",
         "trend20": "Acheter si clôture > SMA20 +0,5 % ; vendre sous SMA20 -0,5 %"}
REPORT_FIELDS = ["strategy","asset","market","label","status","capital_usd",
                 "return_pct","trades","fees_usd","cash_usd","units","position",
                 "price_usd","price_asof","price_source","pricing_quality",
                 "last_event","initial_usd","last_signal_date"]
HISTORY_FIELDS = ["recorded_at",*REPORT_FIELDS]
EVENT_FIELDS = ["id","observed_at","strategy","market","asset","side","status",
                "signal_date","signal_close","quote_at","quote_price","fill_estimate",
                "quantity","gross_usd","fee_usd","net_usd","reason","price_source"]
USER_AGENT = "SeikoTradingLab-Research/1.0 (paper simulation, source may restrict access)"


def safe_number(value):
    n = float(value)
    if not math.isfinite(n) or n <= 0:
        raise ValueError("Missing/nonpositive market price")
    return n


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def cached_market_quotes(now):
    try:
        cache = load_json(CACHE) or {}
        t = datetime.fromisoformat(cache.get("checked_at",""))
        if t.tzinfo and timedelta(0) <= now-t <= timedelta(minutes=40):
            return cache.get("quotes",{}), cache.get("errors",{}), True
    except (ValueError,OSError,TypeError):
        pass
    return None,None,False


def fetch_yahoo(symbol, now):
    """No API key; unofficial source. Missing, stale or malformed quotes never execute."""
    errors=[]
    for host in ("query1.finance.yahoo.com","query2.finance.yahoo.com"):
        try:
            response=requests.get(
                "https://"+host+"/v8/finance/chart/"+quote(symbol,safe=""),
                params={"interval":"1d","range":"3mo","events":"div,splits"},
                headers={"User-Agent":USER_AGENT,"Accept":"application/json"},
                timeout=12)
            response.raise_for_status()
            result=(response.json().get("chart") or {}).get("result") or []
            if len(result)!=1:
                raise ValueError("Missing/unexpected Yahoo chart result")
            x=result[0]
            meta=x.get("meta") or {}
            if meta.get("currency")!="USD" or not x.get("timestamp"):
                raise ValueError("Wrong quote currency or no timestamps")
            tzname=meta.get("exchangeTimezoneName")
            if tzname not in ("America/New_York","US/Eastern"):
                raise ValueError("Unexpected market timezone")
            price=safe_number(meta["regularMarketPrice"])
            quote_at=datetime.fromtimestamp(int(meta["regularMarketTime"]),timezone.utc)
            if quote_at>now+timedelta(minutes=2) or now-quote_at>timedelta(days=7):
                raise ValueError("Quote timestamp outside safe window")
            q=x.get("indicators",{}).get("quote") or []
            if len(q)!=1 or len(q[0].get("close",[]))!=len(x["timestamp"]):
                raise ValueError("Invalid daily OHLC bars")
            bars=[]
            for t,p in zip(x["timestamp"],q[0]["close"]):
                if p is None:continue
                try:
                    d=datetime.fromtimestamp(int(t),MARKET_TZ).date().isoformat()
                    p=safe_number(p)
                    if d <= now.astimezone(MARKET_TZ).date().isoformat():
                        bars.append({"date":d,"close":p})
                except (ValueError,OverflowError):
                    continue
            bars={b["date"]:b for b in bars}
            bars=sorted(bars.values(),key=lambda b:b["date"])
            if len(bars)<22 or len(bars)>100:
                raise ValueError("Insufficient price history")
            session=now.astimezone(MARKET_TZ)
            quote_local=quote_at.astimezone(MARKET_TZ)
            eligible=(session.weekday()<5
                and (9,40) <= (session.hour,session.minute) <= (15,55)
                and (9,30) <= (quote_local.hour,quote_local.minute) <= (15,55)
                and quote_local.date()==session.date()
                and now-quote_at<=timedelta(minutes=35))
            previous=[b for b in bars if b["date"]<session.date().isoformat()]
            if not previous:raise ValueError("No previously completed daily candle")
            return {"symbol":symbol,"source":"Yahoo Finance public chart (unofficial)",
                    "quote_at":quote_at.isoformat(),"price":price,
                    "reference_date":quote_local.date().isoformat(),
                    "eligible":eligible,"bars":bars[-70:],"previous":previous[-60:],
                    "currency":"USD","feed":"delayed/unofficial"}
        except (requests.RequestException,KeyError,TypeError,ValueError,IndexError) as e:
            errors.append(host+": "+str(e)[:110])
    raise ValueError(" | ".join(errors))


def fetch_ecb(now):
    """ECB fixes are informational; never label them executable FX quotes."""
    response=requests.get(
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A",
        params={"format":"csvdata","lastNObservations":"95"},
        headers={"Accept":"text/csv","User-Agent":USER_AGENT},timeout=14)
    response.raise_for_status()
    reader=csv.DictReader(response.text.splitlines())
    if not reader.fieldnames or "TIME_PERIOD" not in reader.fieldnames or "OBS_VALUE" not in reader.fieldnames:
        raise ValueError("Malformed ECB exchange-rate CSV")
    bars=[]
    for row in reader:
        try:
            d=row["TIME_PERIOD"]; datetime.fromisoformat(d)
            v=safe_number(row["OBS_VALUE"])
            if d<=now.astimezone(PAIR_TZ).date().isoformat():bars.append({"date":d,"close":v})
        except (ValueError,KeyError,TypeError):
            continue
    bars=sorted({b["date"]:b for b in bars}.values(),key=lambda b:b["date"])
    if len(bars)<22:raise ValueError("ECB history too short")
    today=now.astimezone(PAIR_TZ).date()
    quote_date=datetime.fromisoformat(bars[-1]["date"]).date()
    if (today-quote_date).days>6:raise ValueError("Stale ECB reference")
    # A newly published reference is already in the API, but is NOT an
    # executable FX bid/ask. All EURUSD fills are clearly indicative.
    earlier=bars[:-1]
    return {"symbol":"EURUSD","source":"ECB daily reference (not executable)",
            "quote_at":(bars[-1]["date"]+"T16:00:00+01:00"),
            "price":bars[-1]["close"],"reference_date":bars[-1]["date"],
            "eligible":quote_date==today and today.weekday()<5,
            "bars":bars[-70:],"previous":earlier[-60:],
            "currency":"USD","feed":"ECB indicative fix"}


def fetch_sources(now):
    cached,old_errors,reused=cached_market_quotes(now)
    if reused:return cached,old_errors
    data={};errors={}
    for symbol,*_ in SPECS:
        try:
            data[symbol]=fetch_ecb(now) if symbol=="EURUSD" else fetch_yahoo(symbol,now)
        except (ValueError,requests.RequestException,KeyError) as exc:
            errors[symbol]=str(exc)[:300]
            # A historic quote may be used for a clearly stale valuation, NEVER orders.
            if cached and symbol in cached:
                old=dict(cached[symbol]);old["eligible"]=False
                data[symbol]=old
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    CACHE.write_text(json.dumps({"checked_at":now.isoformat(),"quotes":data,"errors":errors},
                                ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data,errors


def round_down(value, decimals):
    q=Decimal("1").scaleb(-decimals)
    return float(Decimal(str(value)).quantize(q,rounding=ROUND_DOWN))


def costs(symbol):
    if symbol=="EURUSD":
        return FX_FEE,0,FX_HALF_SPREAD+FX_SLIP,2
    return FEE_RATE,MIN_FEE,HALF_SPREAD+SLIP,0


def fill(side,cash,units,price,symbol):
    """Single observed reference quote with explicit estimated, NOT observed bid/ask."""
    fee_rate,min_fee,impact,precision=costs(symbol)
    if side=="BUY":
        estimated=price*(1+impact)
        raw=(cash-min_fee)/(estimated*(1+fee_rate))
        qty=round_down(max(0,raw),precision)
        if qty<=0:return None,"MINIMUM_QUANTITY_OR_FUNDS"
        gross=qty*estimated
        fee=max(min_fee,gross*fee_rate)
        if gross+fee>cash+1e-7:return None,"INSUFFICIENT_FUNDS"
        return {"qty":qty,"price":estimated,"gross":gross,"fee":fee,
                "net":-(gross+fee)},None
    if units<=0:return None,"NO_POSITION"
    estimated=price*(1-impact)
    gross=units*estimated
    fee=max(min_fee,gross*fee_rate)
    if gross-fee<=0:return None,"COST_EXCEEDS_PROCEEDS"
    return {"qty":units,"price":estimated,"gross":gross,"fee":fee,
            "net":gross-fee},None


def liquidation(cash,units,price,symbol):
    if units<=0:return cash
    fee,min_fee,impact,_=costs(symbol)
    gross=units*price*(1-impact)
    return cash+max(0,gross-max(min_fee,gross*fee))


def evaluate(variant,previous,has_position):
    if variant=="hold":
        return "WAIT" if has_position else "BUY","Conservation longue durée"
    if len(previous)<20:return "WAIT","Historique inférieur à 20 clôtures"
    average=sum(b["close"] for b in previous[-20:])/20
    last=previous[-1]["close"]
    if not has_position and last>average*1.005:
        return "BUY","Clôture %.5f > SMA20 %.5f (+0,5 %)"%(last,average)
    if has_position and last<average*.995:
        return "SELL","Clôture %.5f < SMA20 %.5f (-0,5 %)"%(last,average)
    return "WAIT","Pas de signal confirmé sur 20 jours"


def read_rows(path):
    if not path.exists():return []
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))


def write_rows(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)


def main():
    now=datetime.now(timezone.utc)
    sources,errors=fetch_sources(now)
    if not sources:
        print("Multi-asset: no validated sources. No portfolio initialized.")
        STATUS.parent.mkdir(parents=True,exist_ok=True)
        STATUS.write_text(json.dumps({"checked_at":now.isoformat(),"ready":False,
           "errors":errors,"message":"No data; fail closed"},ensure_ascii=False,indent=2)+"\n",
           encoding="utf-8")
        return
    state=load_json(STATE)
    if state is None:
        state={"schema":1,"created":now.isoformat(),"portfolios":{},
               "last_signal_day":{},"initial_per_strategy_usd":START}
    if state.get("schema")!=1 or state.get("initial_per_strategy_usd")!=START:
        raise ValueError("Incompatible multi-asset state")
    reports=[];new_events=[]
    for symbol,label,market,kind,src in SPECS:
        quote=sources.get(symbol)
        for strategy in ("hold","trend20"):
            key=symbol.lower()+"_"+strategy
            p=state["portfolios"].setdefault(key,{"cash":START,"units":0.0,
                "trades":0,"fees":0.0,"last_price":None,"last_price_at":None})
            status="NO_DATA";priced=None;asof=""
            if quote:
                price=safe_number(quote["price"])
                asof=quote["quote_at"]
                is_recent=(now-datetime.fromisoformat(asof)).total_seconds()<=6*86400
                if is_recent:
                    p["last_price"]=price;p["last_price_at"]=asof
                priced=p.get("last_price")
                status="QUOTE_READY" if quote["eligible"] else "QUOTE_DELAYED_OR_MARKET_CLOSED"
                if not is_recent:status="STALE_QUOTE"
                if quote["eligible"]:
                    previous=quote["previous"]
                    signal_day=previous[-1]["date"] if previous else None
                    if signal_day and state["last_signal_day"].get(key)!=signal_day:
                        action,reason=evaluate(strategy,previous,p["units"]>0)
                        if action in ("BUY","SELL"):
                            execution,rejection=fill(action,p["cash"],p["units"],price,symbol)
                            entry={"id":now.isoformat()+":"+key+":"+action,
                                "observed_at":now.isoformat(),"strategy":key,"market":market,
                                "asset":symbol,"side":action,
                                "status":"SIMULATED_FILL" if execution else rejection,
                                "signal_date":signal_day,"signal_close":previous[-1]["close"],
                                "quote_at":asof,"quote_price":price,"fill_estimate":"",
                                "quantity":"","gross_usd":"","fee_usd":"","net_usd":"",
                                "reason":reason+" | Exécution estimée après signal",
                                "price_source":quote["source"]}
                            if execution:
                                if action=="BUY":
                                    p["cash"]=max(0,p["cash"]+execution["net"])
                                    p["units"]+=execution["qty"]
                                else:
                                    p["cash"]+=execution["net"];p["units"]=0.0
                                p["trades"]+=1;p["fees"]+=execution["fee"]
                                entry.update(fill_estimate=round(execution["price"],7),
                                    quantity=execution["qty"],gross_usd=round(execution["gross"],5),
                                    fee_usd=round(execution["fee"],5),
                                    net_usd=round(execution["net"],5))
                            new_events.append(entry)
                            status="SIMULATED_FILL" if execution else "ORDER_REJECTED"
                        state["last_signal_day"][key]=signal_day
            equity=liquidation(float(p["cash"]),float(p["units"]),
                                float(priced),symbol) if priced is not None else float(p["cash"])
            quality="OBSERVED" if quote and quote["eligible"] else (
                "REFERENCE_ONLY" if symbol=="EURUSD" and quote else
                "DELAYED_OR_CLOSED" if quote else "NO_DATA")
            if quote and status=="STALE_QUOTE":quality="STALE"
            reports.append({"strategy":key,"asset":symbol,"market":market,"label":label,
                "status":status,"capital_usd":round(equity,5),
                "return_pct":round((equity/START-1)*100,4),"trades":p["trades"],
                "fees_usd":round(p["fees"],5),"cash_usd":round(p["cash"],5),
                "units":p["units"],"position":"INVESTED" if p["units"]>0 else "CASH",
                "price_usd":priced or "","price_asof":p.get("last_price_at") or "",
                "price_source":quote["source"] if quote else "",
                "pricing_quality":quality,"last_event":now.isoformat() if status=="SIMULATED_FILL" else "",
                "initial_usd":START,"last_signal_date":state["last_signal_day"].get(key,"")})
    state["updated"]=now.isoformat()
    state["feed_notes"]={"equities":"Yahoo Finance public chart, unofficial, delayed; bid/ask are modeled",
        "forex":"ECB reference is information-only; fill prices not executable",
        "distributions":"Dividends, fund distributions and tax are not yet included"}
    prior_history=read_rows(HISTORY)
    prior_events=read_rows(EVENTS)
    # Snapshots are append-only and all strategies start from the same state timestamp.
    prior_history.extend({"recorded_at":now.isoformat(),**row} for row in reports)
    prior_events.extend(new_events)
    STATE.parent.mkdir(parents=True,exist_ok=True)
    write_rows(LATEST,reports,REPORT_FIELDS)
    write_rows(HISTORY,prior_history,HISTORY_FIELDS)
    write_rows(EVENTS,prior_events,EVENT_FIELDS)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    STATUS.write_text(json.dumps({"checked_at":now.isoformat(),"ready":True,
         "feed_count":len(sources),"feed_errors":errors,"new_events":len(new_events),
         "status_by_asset":{s:("READY" if q["eligible"] else "CLOSED_OR_STALE")
                              for s,q in sources.items()},
         "price_sources":"Yahoo unofficial and ECB reference; execution is hypothetical"},
         ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Multi-asset: sources",len(sources),"/",len(SPECS),
          "strategies",len(reports),"new paper orders",len(new_events),
          "estimated USD",round(sum(float(r["capital_usd"]) for r in reports),3))


if __name__=="__main__":
    main()
