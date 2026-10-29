"""Persistent read-only follow-up of large Ethereum stablecoin transfer addresses.

This is a capped watchlist of public pseudonymous addresses detected in a
bounded Blockscout sample. No owner identity or buy/sell classification.
Preserve monitoring when the latest sample has no large movement.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
import requests
from research.large_transfers import HOST, CONTRACTS, transfer, MIN_UNITS

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"reports/large_transfer_observations.json"
STATE=ROOT/"state/whale_follow_state.json"
OUTPUT=ROOT/"reports/whale_follow.json"
ADDRESS=re.compile(r"^0x[0-9a-f]{40}$")
MAX_WALLETS=4
MAX_PAGE=50
RETENTION_DAYS=7
MAX_REPORTED_NEW=12
MAX_SEEN=300
MAX_AGE_DAYS=7

def load(path):
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):
        return {}

def recent(value,now,days=MAX_AGE_DAYS):
    try:
        stamp=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return stamp.tzinfo is not None and 0 <= (now-stamp).total_seconds() <= days*86400
    except (ValueError,TypeError,OverflowError):
        return False

def candidates(source,now,state=None):
    """Retain selected addresses across quiet samples and bounded outages."""
    tracked=(state or {}).get("tracked",{})
    tracked=tracked if isinstance(tracked,dict) else {}
    chosen=[]
    # Existing state wins over new market samples. TTL is the time since a
    # real successful observation, NOT the time since the address had a large move.
    for address,row in tracked.items():
        if not isinstance(row,dict):
            continue
        key=str(address).lower()
        last=row.get("last_polled_at") or row.get("baseline_at")
        if ADDRESS.fullmatch(key) and recent(last,now) and key not in chosen:
            chosen.append(key)
        if len(chosen)>=MAX_WALLETS:
            return chosen
    if not isinstance(source,dict) or source.get("state") not in ("observing","partial"):
        return chosen
    if not recent(source.get("generated_at"),now,1):
        return chosen
    rows=source.get("sampled_wallet_flows",[])
    if not isinstance(rows,list):
        return chosen
    for row in rows:
        if not isinstance(row,dict) or row.get("identity_verified") is not False:
            continue
        address=str(row.get("address","")).lower()
        if ADDRESS.fullmatch(address) and address not in chosen:
            chosen.append(address)
        if len(chosen)>=MAX_WALLETS:
            break
    return chosen

def fetch_address(address,get=requests.get):
    response=get(HOST+"/addresses/"+address+"/token-transfers",
                 params={"type":"ERC-20"},timeout=15,
                 headers={"User-Agent":"SeikoWhaleFollow/2.0"})
    response.raise_for_status()
    body=response.json()
    if not isinstance(body,dict):
        raise ValueError("Unexpected Blockscout response")
    items=body.get("items")
    if not isinstance(items,list) or len(items)>MAX_PAGE:
        raise ValueError("Invalid bounded Blockscout transfer page")
    return items

def observe(now,source,state,get=requests.get):
    """Keep monitoring previously discovered addresses across empty/partial scans.

    Selection is based on sampled public transfers, NOT a claimed owner.
    Failed provider requests never erase baselines or produce fake new events.
    """
    fresh_candidates=candidates(source,now)
    prior=state.get("tracked",{}) if isinstance(state,dict) else {}
    prior=prior if isinstance(prior,dict) else {}
    retained={}
    for address,detail in prior.items():
        if not ADDRESS.fullmatch(address) or not isinstance(detail,dict):
            continue
        last=detail.get("last_detected_at") or detail.get("baseline_at")
        try:
            last_dt=datetime.fromisoformat(str(last).replace("Z","+00:00"))
            age=(now-last_dt).total_seconds()
            if last_dt.tzinfo and 0<=age<=RETENTION_DAYS*86400:
                retained[address]=detail
        except (TypeError,ValueError,OverflowError):
            continue
    # New discoveries take priority. Existing watches continue when a sample
    # contains no million-unit transfers or a token provider is temporarily down.
    addresses=list(dict.fromkeys(list(retained)+fresh_candidates))[:MAX_WALLETS]
    report={"schema":1,"generated_at":now.isoformat(),
            "state":"observing" if addresses else "no_recent_addresses",
            "source":HOST,"discovery_state":source.get("state","unknown"),
            "selection":"public_sample_not_verified_whale_identity",
            "method":"latest_one_page_per_selected_public_address",
            "coverage":"bounded_non_exhaustive_pseudonymous_addresses",
            "tracked_addresses":[],"new_transfers":[],"errors":{},
            "max_addresses":MAX_WALLETS,"retention_days":RETENTION_DAYS,
            "can_infer_owner":False,"can_infer_trade":False,"real_orders":False}
    if not addresses:
        return report,{"schema":1,"tracked":{}}
    updated={}
    for address in addresses:
        old=retained.get(address)
        discovered=address in fresh_candidates
        baseline=old.get("baseline_at",now.isoformat()) if old else now.isoformat()
        last_detected=now.isoformat() if discovered else old.get("last_detected_at",baseline)
        try:
            rows=fetch_address(address,get)
            valid=[]
            for raw in rows:
                try:
                    if not isinstance(raw,dict):
                        continue
                    token_meta=raw.get("token") or {}
                    if not isinstance(token_meta,dict):
                        continue
                    contract=str(token_meta.get("address_hash","")).lower()
                    token=next((symbol for symbol,value in CONTRACTS.items()
                                if value==contract),None)
                    if token is None:
                        continue
                    item=transfer(raw,token,now)
                    if address not in (item["from_address"],item["to_address"]):
                        continue
                    valid.append(item)
                except (KeyError,TypeError,ValueError,OverflowError,InvalidOperation):
                    continue
            unique={e["id"]:e for e in valid}
            previous=set(old.get("seen_ids",[])) if old else set()
            # First observation only establishes baseline; no fake activity.
            new=[] if old is None else [e for k,e in unique.items()
                                           if k not in previous and Decimal(e["quantity"])>=MIN_UNITS]
            space=max(0,MAX_REPORTED_NEW-len(report["new_transfers"]))
            report["new_transfers"].extend(new[:space])
            report["tracked_addresses"].append({
                "address":address,"verified_identity":False,"sample_count":len(unique),
                "new_count":len(new),"baseline_at":baseline,
                "last_detected_at":last_detected,
                "last_polled_at":now.isoformat(),"collection_state":"ok",
                "monitoring":"active",
                "discovered_this_scan":bool(discovered)})
            updated[address]={
                "baseline_at":baseline,"last_detected_at":last_detected,
                "seen_ids":list(dict.fromkeys((old.get("seen_ids",[]) if old else [])
                                               +list(unique)))[-MAX_SEEN:],
                "last_polled_at":now.isoformat()}
        except (requests.RequestException,ValueError,TypeError,KeyError) as exc:
            # Do not discard an established watch when a provider fails.
            report["errors"][address]=type(exc).__name__
            report["tracked_addresses"].append({
                "address":address,"verified_identity":False,
                "sample_count":None,"new_count":0,"baseline_at":baseline,
                "last_detected_at":last_detected,
                "last_polled_at":old.get("last_polled_at") if old else None,
                "collection_state":"unavailable","monitoring":"temporarily_unavailable",
                "discovered_this_scan":bool(discovered)})
            if old:
                updated[address]=dict(old,last_detected_at=last_detected)
    if len(report["errors"])==len(addresses):
        report["state"]="unavailable"
    elif report["errors"]:
        report["state"]="partial"
    return report,{"schema":1,"tracked":updated}


def main():
    now=datetime.now(timezone.utc)
    report,state=observe(now,load(SOURCE),load(STATE))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if state:
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Whale follow",report["state"],
          "tracked",len(report["tracked_addresses"]),
          "new large transfers",len(report["new_transfers"]))

if __name__=="__main__":
    main()
