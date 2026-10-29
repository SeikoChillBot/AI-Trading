"""Bounded, read-only follow-up of large-transfer addresses from Blockscout.

These are pseudonymous public addresses, NOT verified whale identities.
A transfer is not a purchase/sale; observations cover only one recent API page.
No API key, trade integration or user account access.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from decimal import InvalidOperation
from pathlib import Path
import requests
from research.large_transfers import HOST, CONTRACTS, transfer

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"reports/large_transfer_observations.json"
STATE=ROOT/"state/whale_follow_state.json"
OUTPUT=ROOT/"reports/whale_follow.json"
ADDRESS=re.compile(r"^0x[0-9a-f]{40}$")
MAX_WALLETS=4
MAX_PAGE=50


def load(path):
    try:
        result=json.loads(path.read_text(encoding="utf-8"))
        return result if isinstance(result,dict) else {}
    except (OSError,ValueError):
        return {}


def candidates(source,now):
    if source.get("state") not in ("observing","partial"):
        return []
    try:
        age=(now-datetime.fromisoformat(source["generated_at"])).total_seconds()
        if not 0<=age<=3*3600:
            return []
    except (KeyError,ValueError,TypeError):
        return []
    found=[]
    for row in source.get("sampled_wallet_flows",[]):
        address=str(row.get("address","")).lower()
        if not ADDRESS.fullmatch(address):
            continue
        if row.get("identity_verified") is not False:
            continue
        if address not in found:
            found.append(address)
        if len(found)==MAX_WALLETS:
            break
    return found


def fetch_address(address,get=requests.get):
    response=get(HOST+"/addresses/"+address+"/token-transfers",
                 params={"type":"ERC-20"},timeout=15,
                 headers={"User-Agent":"SeikoWhaleFollow/1.0"})
    response.raise_for_status()
    body=response.json()
    if not isinstance(body,dict):
        raise ValueError("Unexpected Blockscout response")
    items=body.get("items")
    if not isinstance(items,list) or len(items)>MAX_PAGE:
        raise ValueError("Invalid bounded Blockscout transfer page")
    return items


def observe(now,source,state,get=requests.get):
    addresses=candidates(source,now)
    report={"schema":1,"generated_at":now.isoformat(),
            "state":"not_configured" if not addresses else "observing",
            "source":HOST,
            "method":"latest_one_page_per_selected_public_address",
            "coverage":"bounded_non_exhaustive_pseudonymous_addresses",
            "tracked_addresses":[],"new_transfers":[],"errors":{},
            "max_addresses":MAX_WALLETS,"can_infer_owner":False,
            "can_infer_trade":False,"real_orders":False}
    saved=dict(state.get("tracked",{})) if isinstance(state.get("tracked"),dict) else {}
    if not addresses:
        return report,state
    for address in addresses:
        old=saved.get(address)
        try:
            items=fetch_address(address,get)
            valid=[]
            for raw in items:
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
            previous=set(old.get("seen_ids",[])) if isinstance(old,dict) else set()
            # Initial address observation is a baseline, not a new whale alert.
            new=[] if old is None else [e for k,e in unique.items() if k not in previous]
            report["new_transfers"].extend(new[:8])
            report["tracked_addresses"].append({
                "address":address,"verified_identity":False,"sample_count":len(unique),
                "new_count":len(new),"baseline_at":old.get("baseline_at")
                if isinstance(old,dict) else now.isoformat()})
            saved[address]={
                "baseline_at":old.get("baseline_at") if isinstance(old,dict) else now.isoformat(),
                "seen_ids":sorted(previous|set(unique))[-300:],
                "last_polled_at":now.isoformat()}
        except (requests.RequestException,ValueError,TypeError,KeyError) as exc:
            report["errors"][address]=type(exc).__name__
    # Preserve previously observed address history for reappearance, but bound
    # size; no private information and no fictitious balances are produced.
    saved=dict(list(saved.items())[-16:])
    if report["errors"] and not report["tracked_addresses"]:
        report["state"]="unavailable"
    elif report["errors"]:
        report["state"]="partial"
    return report,{"schema":1,"tracked":saved}


def main():
    now=datetime.now(timezone.utc)
    report,state=observe(now,load(SOURCE),load(STATE))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if report["state"]!="not_configured":
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Bounded whale address follow-up:",report["state"],
          "addresses",len(report["tracked_addresses"]),
          "new observations",len(report["new_transfers"]))


if __name__=="__main__":
    main()
