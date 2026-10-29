"""Read-only, bounded Base native USDC Blockscout observations.
Native USDC on Base contract documented by Circle:
https://www.circle.com/blog/usdc-now-available-natively-on-base
This is a public transfer sample, not a verified purchase or wallet identity.
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

def build(now,get=requests.get):
    result={"schema":1,"generated_at":now.isoformat(),"state":"observing",
            "chain":"base","token":"USDC","source":HOST,
            "contract":CONTRACT,"sampled_count":0,"large_count":0,
            "highlights":[],"error":None,"not_exhaustive":True,
            "can_infer_buy_sell":False,"real_orders":False}
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
        result["state"]="unavailable"
        result["error"]=type(error).__name__
    return result

def main():
    output=build(datetime.now(timezone.utc))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Base USDC:",output["state"],output["sampled_count"],
          output["large_count"])

if __name__=="__main__":
    main()
