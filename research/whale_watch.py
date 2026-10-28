"""Read-only ERC-20 transfer observer for explicitly verified public wallets.

Never interprets a token transfer as a buy/sell. No public-wallet identity is
guessed. A first observation is a baseline, not a fresh trading alert.
Requires a user-supplied Etherscan API key AND a verified watchlist entry.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
WATCHLIST=ROOT/"research/whale_watchlist.json"
STATE=ROOT/"state/whale_watch_state.json"
OUTPUT=ROOT/"reports/whale_observations.json"
EVENTS=ROOT/"reports/whale_transfer_events.jsonl"
ENDPOINT="https://api.etherscan.io/v2/api"
ADDRESS=re.compile(r"^0x[0-9a-fA-F]{40}$")
MAX_WALLETS=10

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:return default

def validate_watchlist(data):
    if data.get("schema")!=1 or not isinstance(data.get("wallets"),list):
        raise ValueError("Invalid wallet watchlist")
    seen=set();approved=[]
    for raw in data["wallets"]:
        if not isinstance(raw,dict):raise ValueError("Invalid wallet metadata")
        address=raw.get("address")
        if not isinstance(address,str) or not ADDRESS.fullmatch(address):
            raise ValueError("Invalid Ethereum address; no network guessing")
        # Ownership confidence must be supplied with an auditable citation.
        if raw.get("chainid")!=1 or not raw.get("source_url","").startswith("https://"):
            raise ValueError("Only Ethereum verified-label wallets with source URLs")
        label=str(raw.get("label","")).strip()
        if not label or len(label)>80:raise ValueError("Missing label")
        key=address.lower()
        if key in seen:raise ValueError("Duplicated wallet")
        seen.add(key)
        approved.append({"address":key,"label":label,
                         "source_url":raw["source_url"],"chainid":1})
    if len(approved)>MAX_WALLETS:raise ValueError("Watchlist above safe API quota")
    return approved

def fetch_transfers(address,api_key,get=requests.get):
    resp=get(ENDPOINT,params={"chainid":1,"module":"account",
                "action":"tokentx","address":address,"page":1,
                "offset":75,"sort":"desc","apikey":api_key},timeout=15)
    resp.raise_for_status()
    data=resp.json()
    if data.get("status")=="0" and "No transactions" in str(data.get("message","")):
        return []
    if data.get("status")!="1" or not isinstance(data.get("result"),list):
        raise ValueError("Unverified Etherscan response")
    return data["result"]

def event(row,wallet,now):
    sender=str(row["from"]).lower()
    receiver=str(row["to"]).lower()
    if sender!=wallet["address"] and receiver!=wallet["address"]:
        raise ValueError("Unrelated transfer returned by provider")
    contract=str(row["contractAddress"]).lower()
    if not ADDRESS.fullmatch(contract):
        raise ValueError("Token contract missing")
    decimals=int(row["tokenDecimal"])
    if not 0<=decimals<=36:raise ValueError("Suspicious token precision")
    quantity=Decimal(str(row["value"]))/(Decimal(10)**decimals)
    if quantity<0:raise ValueError("Negative transfer quantity")
    t=int(row["timeStamp"])
    if t>now.timestamp()+180 or t<1e9:raise ValueError("Invalid transfer timestamp")
    tx=str(row["hash"]).lower()
    if not re.fullmatch(r"0x[0-9a-f]{64}",tx):
        raise ValueError("Invalid transaction hash")
    fingerprint=hashlib.sha256(("|".join([wallet["address"],tx,
        str(row.get("logIndex","")),contract,sender,receiver,
        str(row["value"])] )).encode()).hexdigest()
    return {"id":fingerprint,"wallet":wallet["address"],"label":wallet["label"],
            "label_source":wallet["source_url"],
            "timestamp":datetime.fromtimestamp(t,timezone.utc).isoformat(),
            "tx_hash":tx,"contract":contract,
            "token_symbol_unverified":str(row.get("tokenSymbol",""))[:24],
            "quantity":str(quantity),
            "direction":"out" if sender==wallet["address"] else "in",
            "classification":"ERC20_TRANSFER_ONLY_NOT_A_TRADE",
            "usd_value":None,"trade_inference":"unknown"}

def build(now,key,watchlist,state,get=requests.get):
    wallets=validate_watchlist(watchlist)
    output={"schema":1,"generated_at":now.isoformat(),
            "state":"not_configured","wallets_configured":len(wallets),
            "tracked":[],"new_transfer_events":[],"errors":{},
            "can_infer_buy_sell":False,"trades_executed":0,
            "warning":"Transfer does not prove a purchase, sale or wallet owner's identity."}
    if not wallets or not key:return output,state
    state=dict(state)
    previous=dict(state.get("addresses",{}))
    output["state"]="observing"
    for wallet in wallets:
        address=wallet["address"]
        try:
            raw=fetch_transfers(address,key,get)
            parsed=[event(row,wallet,now) for row in raw]
            observed={p["id"] for p in parsed}
            old=previous.get(address)
            if old is None:
                # Initial sighting is not historical PnL or new whale activity.
                new=[]
                previous[address]={"seen_ids":sorted(observed),
                                   "baseline_at":now.isoformat()}
            else:
                known=set(old.get("seen_ids",[]))
                new=[p for p in parsed if p["id"] not in known]
                previous[address]={"seen_ids":sorted(observed|known)[-300:],
                                   "baseline_at":old.get("baseline_at")}
            output["new_transfer_events"].extend(new)
            output["tracked"].append({"address":address,"label":wallet["label"],
                                      "last_seen_count":len(parsed),
                                      "new_observed_count":len(new)})
        except (KeyError,ValueError,TypeError,InvalidOperation,requests.RequestException) as exc:
            output["errors"][address]=type(exc).__name__+": "+str(exc)[:160]
    state["schema"]=1;state["addresses"]=previous
    if output["errors"]:output["state"]="partial"
    return output,state

def main():
    now=datetime.now(timezone.utc)
    key=os.environ.get("ETHERSCAN_API_KEY","")
    watchlist=load(WATCHLIST,{"schema":1,"wallets":[]})
    current=load(STATE,{"schema":1,"addresses":{}})
    output,new_state=build(now,key,watchlist,current)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    if output["state"]!="not_configured":
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(new_state,indent=2)+"\n",encoding="utf-8")
        if output["new_transfer_events"]:
            with EVENTS.open("a",encoding="utf-8") as file:
                for observation in output["new_transfer_events"]:
                    file.write(json.dumps(observation,ensure_ascii=False)+"\n")
    print("Whale observer:",output["state"],"configured wallets:",
          output["wallets_configured"],"new transfers:",
          len(output["new_transfer_events"]))

if __name__=="__main__":
    main()
