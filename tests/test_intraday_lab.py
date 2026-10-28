"""Deterministic tests: hourly OOS proof, source hygiene and no instant gains."""
import unittest
from datetime import datetime,timezone,timedelta
from research import intraday_lab as lab

NOW=datetime(2026,10,29,0,0,tzinfo=timezone.utc)
START=int(NOW.timestamp())-510*3600

def bars(n=508):
    return [{"t":START+i*3600,
             "open":100+i*.04,"close":100+i*.04+.01} for i in range(n)]

class Response:
    def __init__(self,symbol):self.symbol=symbol
    def raise_for_status(self):pass
    def json(self):
        sample=[[b["t"],str(b["open"]),"1","1",str(b["close"]),"0","0","0"] for b in bars()]
        return {"error":[],"result":{self.symbol:sample,"last":0}}

def fetch(url,params,**kwargs):
    return Response(params["pair"])

class IntradaySafetyTests(unittest.TestCase):
    def test_fetch_requires_closed_contiguous_hours(self):
        b=lab.fetch("BTCUSD",NOW,fetch)
        self.assertEqual(len(b),508)
        self.assertLess(b[-1]["t"]+3600,NOW.timestamp())

    def test_oos_no_lookahead_and_immutable_registration(self):
        b=bars()
        p=lab.choose(b,0,240)
        self.assertIn(p,lab.GRID)
        result=lab.evidence(b)
        self.assertEqual(len(result["folds"]),2)
        self.assertFalse(result["proven_profitable"])
        cand=lab.create_candidate(b,NOW)
        self.assertEqual(cand["capital_usd"],20.0)
        self.assertEqual(cand["observations"],0)
        self.assertEqual(cand["state"],"waiting_for_future_hour")

    def test_default_paper_study_no_orders_no_backfill(self):
        result,state=lab.build(NOW,get=fetch)
        self.assertEqual(set(result["assets"]),{"BTCUSD","ETHUSD","SOLUSD"})
        self.assertFalse(result["real_orders"])
        self.assertEqual(result["funds_real_usd"],0)
        self.assertTrue(all(x["paper_forward"]["observations"]==0
                            for x in result["assets"].values()))
        second,_=lab.build(NOW,get=fetch,old=state)
        self.assertTrue(all(x["paper_forward"]["observations"]==0
                            for x in second["assets"].values()))

    def test_stale_source_does_not_fabricate_success(self):
        def broken(*a,**kw):raise lab.requests.ConnectionError("No network")
        result,_=lab.build(NOW,get=broken)
        self.assertEqual(result["status"],"unavailable")
        self.assertEqual(result["assets"],{})
        self.assertEqual(len(result["errors"]),3)

if __name__=="__main__":unittest.main()
