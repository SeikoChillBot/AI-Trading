import unittest
from research.strategy_forward_charts import build

class ForwardChartsTests(unittest.TestCase):
    def test_observed_only_no_backfill_and_same_candle_no_duplicate(self):
        forward={"schema":1,"real_orders":False,"robots_modified":False,
                 "generated_at":"2026-11-12","trials":[{"id":"a"}]}
        positions={"schema":1,"tracks":{"a":{"id":"a","last_t":100,
                   "observed_days":1,"value_usd":19.4,"hold_net_pct":-5}}}
        report,state=build(forward,positions,{})
        self.assertEqual(len(report["series"]["a"]),1)
        again,state=build(forward,positions,state)
        self.assertEqual(len(again["series"]["a"]),1)
        positions["tracks"]["a"].update(last_t=200,value_usd=20.5,observed_days=2)
        later,_=build(forward,positions,state)
        self.assertEqual(len(later["series"]["a"]),2)
        self.assertEqual(later["series"]["a"][0]["equity_usd"],19.4)
        self.assertFalse(later["real_orders"])
    def test_unverified_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            build({"schema":1,"real_orders":True,"robots_modified":False},
                  {"schema":1,"tracks":{}},{})

if __name__=="__main__":
    unittest.main()
