"""Daily close observations; signals execute only on the next observed close."""
import json
import math
import sqlite3
from datetime import date

FEE = 0.009
CAPITAL = 20.0

def cycle(db, observation):
    day = date.fromisoformat(observation["last_closed_day"]).isoformat()
    asset = observation["asset"]
    price = float(observation["last_close_usd"])
    change = float(observation["change_7d_pct"])
    if not math.isfinite(price) or price <= 0 or not math.isfinite(change):
        raise ValueError("Invalid observation")
    with sqlite3.connect(db) as con:
        con.execute("BEGIN IMMEDIATE")
        con.execute("""CREATE TABLE IF NOT EXISTS v2_daily
          (asset TEXT, day TEXT, price REAL, cash REAL, units REAL,
           hold_units REAL, signal INTEGER, fees REAL, equity REAL,
           hold_equity REAL, PRIMARY KEY(asset,day))""")
        old = con.execute("SELECT day,cash,units,hold_units,signal,fees FROM v2_daily WHERE asset=? ORDER BY day DESC LIMIT 1",(asset,)).fetchone()
        if old and day <= old[0]:
            return False
        cash, units, hold, fees = CAPITAL, 0., CAPITAL*(1-FEE)/price, 0.
        if old:
            _,cash,units,hold,signal,fees = old
            if signal and not units:
                fees += cash*FEE
                units,cash = cash*(1-FEE)/price,0.
            elif not signal and units:
                gross = units*price
                fees += gross*FEE
                cash,units = gross*(1-FEE),0.
        signal = int(change > 0)
        con.execute("INSERT INTO v2_daily VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (asset,day,price,cash,units,hold,signal,fees,
                     cash+units*price*(1-FEE),hold*price*(1-FEE)))
    return True

def report(db):
    with sqlite3.connect(db) as con:
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute("SELECT * FROM v2_daily ORDER BY asset,day")]
    return {"simulation_only":True,"capital_per_asset":CAPITAL,"fee_per_side":FEE,
            "strategy":"positive seven-day momentum, next observation execution",
            "observations":rows,"qualified":False}

if __name__ == "__main__":
    import sys
    from pathlib import Path
    data=json.loads(Path(sys.argv[2]).read_text())
    for asset,obs in data["latest"]["assets"].items():
        cycle(sys.argv[1],dict(obs,asset=asset))
    print(json.dumps(report(sys.argv[1]),allow_nan=False))
