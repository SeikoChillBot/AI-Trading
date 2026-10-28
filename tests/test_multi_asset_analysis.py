import unittest
from analyze_multi_asset import drawdown, complete_trades, build_report


class MultiAssetAnalysisTests(unittest.TestCase):
    def test_observed_drawdown(self):
        self.assertAlmostEqual(drawdown([1000,1100,990]),10.0)
    def test_complete_trade_uses_net_cash_flows(self):
        logs=[{"status":"SIMULATED_FILL","side":"BUY","net_usd":"-900"},
              {"status":"SIMULATED_FILL","side":"SELL","net_usd":"945"},
              {"status":"MINIMUM_QUANTITY_OR_FUNDS","side":"BUY","net_usd":""}]
        self.assertEqual(complete_trades(logs),[45.0])
    def test_fractional_fills_count_in_closed_trades(self):
        events=[{"status":"SIMULATED_FILL_FRACTIONAL_UNVERIFIED","side":"BUY","net_usd":"-19.9"},
                {"status":"SIMULATED_FILL_FRACTIONAL_UNVERIFIED","side":"SELL","net_usd":"19.8"}]
        self.assertEqual(len(complete_trades(events)),1)

    def test_report_sample_never_qualified_on_day_one(self):
        from datetime import datetime,timezone
        stamp=datetime.now(timezone.utc).isoformat()
        state={"schema":2,"initial_per_strategy_usd":20,"created":stamp,"updated":stamp}
        rows=[{"strategy":str(i)+"_hold","asset":"TEST","market":"action",
               "capital_usd":"20","initial_usd":"20","pricing_quality":"NO_DATA",
               "fees_usd":"0","position":"CASH"} for i in range(18)]
        report=build_report(rows,[],[],state)
        self.assertEqual(report["evaluated_count"],0)
        self.assertEqual(report["capital_usd"],360)
        self.assertEqual(len(report["strategies"]),18)

if __name__=="__main__":
    unittest.main()
