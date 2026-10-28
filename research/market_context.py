"""Independent market context collection for Seiko research, never trading signals.

Fetches dated public DeFi and sentiment observations. A large on-chain transfer
is NOT an authenticated purchase/sale. No portfolio state is touched here.
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"reports/market_context.json"
CHAINS=("Ethereum","Solana","Base","Arbitrum","BSC")
SOURCES={
 "sentiment":"https://api.alternative.me/fng/?limit=2",
 "chain_tvl":"https://api.llama.fi/v2/chains",
 "stablecoins":"https://stablecoins.llama.fi/stablecoins?includePrices=true",
}

def finite(v):
    value=float(v)
    if not math.isfinite(value) or value<0:
        raise ValueError("Non-finite/negative market observation")
    return value

def fear_greed(data,now):
    entries=data.get("data")
    if not isinstance(entries,list) or not entries:
        raise ValueError("No sentiment observations")
    first=entries[0]
    score=int(first["value"]);stamp=int(first["timestamp"])
    if not 0<=score<=100 or not 0<=now.timestamp()-stamp<=4*86400:
        raise ValueError("Sentiment missing, future or stale")
    return {"index":score,"classification":str(first.get("value_classification",""))[:50],
            "published_at":datetime.fromtimestamp(stamp,timezone.utc).isoformat(),
            "source":SOURCES["sentiment"],"kind":"market_sentiment_not_forecast"}

def chain_tvl(data):
    if not isinstance(data,list):raise ValueError("Malformed DeFiLlama chain list")
    indexed={}
    for obj in data:
        if not isinstance(obj,dict):continue
        name=obj.get("name")
        if name in CHAINS:
            indexed[name]=round(finite(obj["tvl"]),2)
    if "Ethereum" not in indexed or "Solana" not in indexed:
        raise ValueError("Missing ETH/SOL chain values")
    return {"tvl_usd_by_chain":indexed,"source":SOURCES["chain_tvl"],
            "kind":"defi_tvl_not_capital_inflow"}

def stablecoin_supply(data):
    items=data.get("peggedAssets") if isinstance(data,dict) else None
    if not isinstance(items,list) or len(items)<5:
        raise ValueError("Invalid stablecoin snapshot")
    usd=0.;included=0
    for coin in items:
        if not isinstance(coin,dict):continue
        circulating=coin.get("circulating") or {}
        amount=circulating.get("peggedUSD")
        if amount is None:continue
        usd+=finite(amount);included+=1
    if included<3 or not 1e7<usd<1e15:
        raise ValueError("Stablecoin total implausible")
    return {"circulating_usd_estimate":round(usd,2),
            "stablecoins_included":included,
            "source":SOURCES["stablecoins"],
            "kind":"stablecoin_supply_not_immediate_buying_pressure"}

def build(now,get=requests.get):
    report={"schema":1,"generated_at":now.isoformat(),
            "model":"market_context_observation_v1",
            "auto_trading":False,"whale_purchases_inferred":False,
            "observations":{},"errors":{},
            "limitations":["TVL is not the same as inflow or investment return.",
               "Stablecoin issuance does not prove an upcoming asset purchase.",
               "A wallet transfer cannot by itself establish a buy or a sale.",
               "Do not compare current readings to past values without point-in-time history."]}
    readers={"sentiment":fear_greed,"chain_tvl":chain_tvl,
             "stablecoins":stablecoin_supply}
    for label,url in SOURCES.items():
        try:
            response=get(url,timeout=12,
                         headers={"User-Agent":"SeikoQuantResearch/1.0"})
            response.raise_for_status()
            raw=response.json()
            report["observations"][label]=(readers[label](raw,now)
                                            if label=="sentiment" else readers[label](raw))
        except (ValueError,TypeError,KeyError,requests.RequestException) as exc:
            report["errors"][label]=type(exc).__name__+": "+str(exc)[:160]
    return report

def main():
    now=datetime.now(timezone.utc)
    result=build(now)
    OUTPUT.parent.mkdir(exist_ok=True,parents=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print("Market observations:",len(result["observations"]),
          "sources,",len(result["errors"]),"unavailable; no trades")

if __name__=="__main__":
    main()
