"""Chronological test cases, synthetic candles only."""
import math
import unittest
from datetime import datetime, timezone
from research import walkforward as wf

def sample(count=480):
    base=1760000000
    base-=base%86400
    return [{"t":base+i*86400,
             "open":100*(1+.0007*i+.01*math.sin(i/15)),
             "close":100*(1+.0007*i+.01*math.sin((i+1)/15))}
            for i in range(count)]

class WalkForwardTests(unittest.TestCase):
    def test_prior_close_only(self):
        bars=sample()
        p={"window":20,"buffer":.005}
        old=wf.signal(bars,100,p,False)
        bars[100]["open"]*=100
        bars[100]["close"]*=100
        self.assertEqual(old,wf.signal(bars,100,p,False))

    def test_more_fees_reduce_hold_performance(self):
        bars=sample()
        self.assertLess(wf.hold(bars,240,300,cost=wf.COST*2),
                        wf.hold(bars,240,300,cost=wf.COST))

    def test_fold_boundaries_and_labels(self):
        bars=sample()
        res=wf.walkforward(bars)
        self.assertGreaterEqual(res["fold_count"],2)
        for fold in res["folds"]:
            self.assertLess(fold["train_last"],fold["test_first"])
            self.assertLess(fold["test_first"],fold["test_last"])
        self.assertEqual(res["status"],"research_only_not_proven")

    def test_missing_bars_are_rejected(self):
        bars=sample()
        now=datetime.fromtimestamp(bars[-1]["t"]+86400+3600,timezone.utc)
        wf.validate(bars,now)
        gap=list(bars)
        gap.pop(50)
        with self.assertRaises(ValueError):wf.validate(gap,now)
        with self.assertRaises(ValueError):wf.validate(bars[:-160],now)

    def test_research_results_never_claim_actual_trades(self):
        bars=sample()
        now=datetime.fromtimestamp(bars[-1]["t"]+86400+3600,timezone.utc)
        report,snapshots=wf.build(now,lambda asset,t:bars)
        self.assertEqual(report["candidate_count"],3)
        self.assertFalse(report["real_orders"])
        self.assertFalse(report["live_strategy_changes"])
        self.assertEqual(len(snapshots),3)

if __name__=="__main__":
    unittest.main()
