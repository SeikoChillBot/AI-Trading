"""Offline unit tests: no Kraken connection or actual orders."""
import unittest
from realistic_sim import (executable_buy, executable_sell, estimated_liquidation,
                           rounded_quantity, START_CASH, TAKER_FEE, SLIPPAGE)

BOOK = {"asks": [(100.2,100.0),(101.0,200.0)],
        "bids": [(100.0,100.0),(99.8,200.0)],
        "spread_pct":0.1998}
RULES = {"min_base":0.01, "min_cost_usd":0.5, "lot_decimals":5}

class RealisticExecutionTests(unittest.TestCase):
    def test_buy_taker_fee_and_no_overdraft(self):
        fill, reason = executable_buy(START_CASH,BOOK,RULES)
        self.assertIsNone(reason)
        self.assertGreater(fill["units"],0)
        self.assertLessEqual(fill["gross"]+fill["fee"],START_CASH+1e-7)
        self.assertAlmostEqual(fill["fee"],fill["gross"]*TAKER_FEE,places=7)
        self.assertGreater(fill["price"],BOOK["asks"][0][0])
    def test_below_base_minimum_is_rejected(self):
        restrictive = dict(RULES, min_base=0.5)
        fill, reason = executable_buy(START_CASH,BOOK,restrictive)
        self.assertIsNone(fill)
        self.assertEqual(reason,"MINIMUM_VOLUME")
    def test_no_liquidity_means_no_fill(self):
        sparse=dict(BOOK, asks=[(100.2,0.001)])
        fill, reason = executable_buy(START_CASH,sparse,RULES)
        self.assertIsNone(fill)
        self.assertEqual(reason,"DEPTH_INSUFFICIENT")
    def test_sell_is_less_than_gross_bid(self):
        fill, reason = executable_sell(0.1,BOOK,RULES)
        self.assertIsNone(reason)
        self.assertLess(fill["net"],10.0)
        self.assertGreater(fill["fee"],0)
    def test_mark_includes_unrealized_sale_cost(self):
        equity=estimated_liquidation({"cash":0,"units":0.1},BOOK)
        self.assertLess(equity,10.0)
        self.assertGreater(equity,9.0)
    def test_round_down_never_round_up(self):
        self.assertEqual(rounded_quantity(0.123456789,4),0.1234)
    def test_min_cost_is_enforced(self):
        limits=dict(RULES,min_cost_usd=40.0)
        fill,reason=executable_buy(20.0,BOOK,limits)
        self.assertIsNone(fill)
        self.assertEqual(reason,"MINIMUM_COST")

if __name__=="__main__":
    unittest.main()
