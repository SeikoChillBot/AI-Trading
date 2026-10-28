"""Offline coverage for paper-only multi-market fill and fail-closed logic."""
import csv
import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
import multi_asset_sim as sim


class MultiAssetTests(unittest.TestCase):
    def test_full_share_order_rejects_if_too_small(self):
        fill, reason=sim.fill("BUY",100,0,700,"SPY")
        self.assertIsNone(fill)
        self.assertEqual(reason,"MINIMUM_QUANTITY_OR_FUNDS")

    def test_fee_spread_slip_and_cash(self):
        order,reason=sim.fill("BUY",1000,0,235,"AAPL")
        self.assertIsNone(reason)
        self.assertEqual(order["qty"],4)
        self.assertGreater(order["price"],235)
        self.assertGreaterEqual(order["fee"],1)
        self.assertLessEqual(-order["net"],1000)
        self.assertLess(sim.liquidation(1000+order["net"],order["qty"],235,"AAPL"),1000)

    def test_sell_has_cost_and_no_leverage(self):
        order,reason=sim.fill("SELL",0,3,100,"BND")
        self.assertIsNone(reason)
        self.assertLess(order["net"],300)
        self.assertGreater(order["fee"],0)

    def test_daily_signals_only_use_completed_candles(self):
        older=[{"date":"2026-09-%02d"%i,"close":100} for i in range(1,21)]
        action,reason=sim.evaluate("trend20",older,False)
        self.assertEqual(action,"WAIT")
        older[-1]["close"]=103
        action,reason=sim.evaluate("trend20",older,False)
        self.assertEqual(action,"BUY")
        action,reason=sim.evaluate("hold",older,False)
        self.assertEqual(action,"BUY")
        action,reason=sim.evaluate("hold",older,True)
        self.assertEqual(action,"WAIT")

    def test_missing_data_cannot_erase_held_assets(self):
        t=datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            files={"STATE":root/"state.json","LATEST":root/"latest.csv",
                   "HISTORY":root/"history.csv","EVENTS":root/"events.csv",
                   "STATUS":root/"status.json","CACHE":root/"cache.json"}
            portfolio={}
            for sym,*_ in sim.SPECS:
                for variant in sim.RULES:
                    portfolio[sym.lower()+"_"+variant]={"cash":1000.0,"units":0,
                        "trades":0,"fees":0,"last_price":None,"last_price_at":None}
            portfolio["aapl_hold"].update({"cash":10,"units":4,"trades":1,
                "fees":1,"last_price":250,"last_price_at":(t-timedelta(days=2)).isoformat()})
            data={"schema":1,"created":t.isoformat(),"portfolios":portfolio,
                  "last_signal_day":{},"initial_per_strategy_usd":1000}
            files["STATE"].write_text(json.dumps(data))
            from contextlib import ExitStack
            with ExitStack() as stack:
                for name,path in files.items():stack.enter_context(patch.object(sim,name,path))
                stack.enter_context(patch.object(sim,"fetch_sources",return_value=(
                    {"BND":{"symbol":"BND","source":"test","price":75,
                      "quote_at":t.isoformat(),"reference_date":t.date().isoformat(),
                      "eligible":False,"bars":[],"previous":[]}},{"AAPL":"unavailable"})))
                sim.main()
            with files["LATEST"].open(newline="",encoding="utf8") as f:
                rows={r["strategy"]:r for r in csv.DictReader(f)}
            self.assertEqual(len(rows),len(sim.SPECS)*2)
            self.assertGreater(float(rows["aapl_hold"]["capital_usd"]),10)
            self.assertEqual(rows["aapl_hold"]["pricing_quality"],"STALE")
            self.assertEqual(float(rows["aapl_hold"]["units"]),4.0)

    def test_cached_quote_cannot_trade_after_close(self):
        now=datetime(2026,10,28,19,45,tzinfo=timezone.utc)
        quote={"symbol":"AAPL","eligible":True,"quote_at":
               datetime(2026,10,28,19,30,tzinfo=timezone.utc).isoformat()}
        self.assertTrue(sim.quote_still_executable(quote,now))
        self.assertFalse(sim.quote_still_executable(
            quote,datetime(2026,10,28,20,10,tzinfo=timezone.utc)))
        self.assertFalse(sim.quote_still_executable(
            quote,now+timedelta(days=1)))

    def test_no_feed_does_not_start_fake_portfolios(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(sim,"STATE",root/"state.json"),patch.object(
                sim,"STATUS",root/"status.json"),patch.object(
                sim,"fetch_sources",return_value=({},{"AAPL":"blocked"})):
                sim.main()
            self.assertFalse((root/"state.json").exists())
            self.assertFalse((root/"latest.csv").exists())

if __name__=="__main__":
    unittest.main()
