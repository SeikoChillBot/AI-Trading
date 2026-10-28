import unittest
from analyze_realistic import drawdown, roundtrips

class StrategyEvaluationTests(unittest.TestCase):
    def test_drawdown_from_initial_balance(self):
        self.assertEqual(drawdown([20,22,18,21]),round((22-18)/22*100,4))
    def test_completed_trade_fees_are_already_reflected(self):
        orders=[
            {"status":"FILLED_SIMULATED","side":"BUY","net_usd":"-20"},
            {"status":"FILLED_SIMULATED","side":"SELL","net_usd":"21"},
            {"status":"FILLED_SIMULATED","side":"BUY","net_usd":"-20"},
            {"status":"FILLED_SIMULATED","side":"SELL","net_usd":"19"},
        ]
        trades=roundtrips(orders)
        self.assertEqual(len(trades),2)
        self.assertAlmostEqual(trades[0]["profit_usd"],1.0)
        self.assertAlmostEqual(trades[1]["profit_usd"],-1.0)
    def test_rejections_do_not_count_as_roundtrips(self):
        events=[
            {"status":"MINIMUM_VOLUME","side":"BUY","net_usd":""},
            {"status":"FILLED_SIMULATED","side":"BUY","net_usd":"-20"},
        ]
        self.assertEqual(roundtrips(events),[])

if __name__=="__main__":
    unittest.main()
