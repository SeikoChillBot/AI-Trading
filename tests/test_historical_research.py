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
