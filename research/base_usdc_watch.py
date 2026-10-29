"""Read-only, bounded Base USDC transfers from public Ethereum-compatible sources.
Circle source: https://www.circle.com/blog/usdc-now-available-natively-on-base
Try Blockscout first; if it denies anonymous access, sample only 12 recent
blocks via Base public JSON-RPC. No API fee or key; rate limits may interrupt.
This is not continuous surveillance, a purchase, or a wallet identification.
"""
from __future__ import annotations
import json
import re
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
HOST="https://base.blockscout.com/api/v2"
CONTRACT="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
OUTPUT=ROOT/"reports/base_usdc_observations.json"
AMOUNT=Decimal("1000000")
TX=re.compile(r"0x[0-9a-f]{64}")


# Official Base public JSON-RPC is free but rate-limited. Limit to 12 recent
# blocks per research cycle: this is explicitly NOT continuous surveillance.
RPC="https://mainnet.base.org"
EVENT_TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
MAX_RPC_BLOCKS=12
MAX_RPC_LOGS=500

def rpc_call(method,params,post):
    response=post(RPC,json={"jsonrpc":"2.0","id":1,"method":method,
                             "params":params},timeout=12,
                  headers={"User-Agent":"AIT-BaseUSDC/1.1"})
    response.raise_for_status()
    body=response.json()
    if not isinstance(body,dict) or body.get("error") is not None:
        raise ValueError("Invalid Base public RPC response")
    return body["result"]

def observe_rpc(now,post):
    latest=int(rpc_call("eth_blockNumber",[],post),16)
    start=max(0,latest-MAX_RPC_BLOCKS+1)
    logs=rpc_call("eth_getLogs",[{"fromBlock":hex(start),"toBlock":hex(latest),
            "address":CONTRACT,"topics":[EVENT_TRANSFER]}],post)
    if not isinstance(logs,list) or len(logs)>MAX_RPC_LOGS:
        raise ValueError("Unbounded Base RPC log response")
    found=[]
    seen=set()
    for row in logs:
        try:
            if not isinstance(row,dict) or str(row.get("address","")).lower()!=CONTRACT:
                continue
            topics=row.get("topics") or []
            if len(topics)!=3 or str(topics[0]).lower()!=EVENT_TRANSFER:
                continue
            amount=Decimal(int(row["data"],16))/Decimal(1000000)
            tx=str(row.get("transactionHash","")).lower()
            log_index=int(row["logIndex"],16)
            block=int(row["blockNumber"],16)
            key=(tx,log_index)
            if not TX.fullmatch(tx) or not amount.is_finite() or amount<AMOUNT or key in seen:
                continue
            if block<start or block>latest:
                continue
            seen.add(key)
            found.append({"tx_hash":tx,"timestamp":None,"block_number":block,
                          "nominal_usd_approx":float(amount),"token":"USDC",
                          "trade_inference":"unknown"})
        except (ValueError,KeyError,TypeError,OverflowError,ArithmeticError):
            continue
    return {"sampled_count":len(logs),"large_count":len(found),
            "highlights":sorted(found,key=lambda r:r["nominal_usd_approx"],reverse=True)[:4],
            "source":RPC,"source_method":"public_rpc_logs",
            "coverage":"last_12_blocks_only","sampled_blocks":latest-start+1}

def build(now,get=requests.get,post=requests.post):
    result={"schema":1,"generated_at":now.isoformat(),"state":"observing",
            "chain":"base","token":"USDC","source":HOST,
            "contract":CONTRACT,"sampled_count":0,"large_count":0,
            "highlights":[],"error":None,"not_exhaustive":True,
            "can_infer_buy_sell":False,"real_orders":False,
            "source_method":"blockscout_explorer_page","coverage":"one_recent_page_only"}
    try:
        response=get(HOST+"/tokens/"+CONTRACT+"/transfers",timeout=12,
                     headers={"User-Agent":"AIT-BaseUSDC/1.0"})
        response.raise_for_status()
        body=response.json()
        rows=body.get("items") if isinstance(body,dict) else None
        if not isinstance(rows,list) or len(rows)>50:
            raise ValueError("Invalid public token transfer sample")
        result["sampled_count"]=len(rows)
        seen=set()
        for row in rows:
            try:
                token=row["token"]
                units=row["total"]
                if (str(token["address_hash"]).lower()!=CONTRACT
                    or int(units["decimals"])!=6):
                    continue
                quantity=Decimal(str(units["value"]))/Decimal(1000000)
                if not quantity.is_finite() or quantity<AMOUNT:
                    continue
                when=datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
                age=(now-when).total_seconds()
                h=str(row.get("transaction_hash") or "").lower()
                if not 0<=age<=86400 or not TX.fullmatch(h) or h in seen:
                    continue
                seen.add(h)
                result["highlights"].append({
                    "tx_hash":h,"timestamp":when.isoformat(),
                    "nominal_usd_approx":float(quantity),
                    "token":"USDC","trade_inference":"unknown"})
            except (KeyError,ValueError,TypeError,ArithmeticError,OverflowError):
                continue
        result["large_count"]=len(result["highlights"])
        result["highlights"]=sorted(result["highlights"],
          key=lambda row:row["nominal_usd_approx"],reverse=True)[:4]
    except (requests.RequestException,KeyError,TypeError,ValueError) as error:
        result["error"]=type(error).__name__
        try:
            # Public explorer access may be restricted; no paid API key used.
            result.update(observe_rpc(now,post))
            result["state"]="observing"
            result["error"]=None
        except (requests.RequestException,ValueError,TypeError,KeyError,OverflowError) as fallback_error:
            result["state"]="unavailable"
            result["error"]=type(error).__name__+"; RPC "+type(fallback_error).__name__
    return result

def main():
    output=build(datetime.now(timezone.utc))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Base USDC:",output["state"],output["sampled_count"],
          output["large_count"])

if __name__=="__main__":
    main()
