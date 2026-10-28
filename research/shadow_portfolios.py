"""Forward-only shadow challengers, independent from 36 running paper robots."""
from __future__ import annotations
import json
from pathlib import Path
import math
from datetime import datetime,timezone
from realistic_sim import pair_metadata,orderbook,executable_buy,executable_sell,estimated_liquidation
from research.walkforward import signal

ROOT=Path(__file__).resolve().parents[1]
BACKTEST=ROOT/"reports/challenger_walkforward.json"
MARKET=ROOT/"reports/challenger_candles.json"
STATE=ROOT/"state/shadow_challenger_portfolios.json"
REPORT=ROOT/"reports/shadow_challengers.json"
HISTORY=ROOT/"reports/shadow_challenger_history.jsonl"
ORDERS=ROOT/"reports/shadow_challenger_orders.jsonl"
START=20.

def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def append(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row,ensure_ascii=False)+"\n")
