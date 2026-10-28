"""Offline walk-forward registration and frozen prospective paper execution."""
import unittest
from datetime import datetime, timezone
from research import challenger_incubator as inc
from research import walkforward as wf

def fixture():
    start=1740009600
    bars=[{"t":start+86400*i,"open":100+i/10,"close":100+i/10}
          for i in range(400)]
    t=datetime.fromtimestamp(bars[-1]["t"]+86400+3600,timezone.utc)
    report={"model":"kraken_daily_walkforward_v1",
            "instruments":{"BTCUSD":{"candidate_parameters":{"window":20,"buffer":.01}}}}
    return bars,t,report

class IncubatorTests(unittest.TestCase):
    def test_first_registration_no_historical_profit(self):
        bars,now,report=fixture()
        result,state=inc.build(now,{"BTCUSD":bars},report,{})
        self.assertEqual(result["assets"]["BTCUSD"]["equity_usd"],20)
        self.assertEqual(result["assets"]["BTCUSD"]["observations"],0)
        self.assertEqual(result["new_history"],[])
        self.assertFalse(result["automatic_promotion"])
        self.assertFalse(result["real_orders"])
        self.assertFalse(result["gemini_code_execution"])
        self.assertEqual(state["active"]["BTCUSD"]["last_processed_t"],bars[-1]["t"])

    def test_new_closed_candle_and_idempotence(self):
        bars,now,report=fixture()
        result,state=inc.build(now,{"BTCUSD":bars},report,{})
        advanced=bars+[{"t":bars[-1]["t"]+86400,"open":143,"close":144}]
        later=datetime.fromtimestamp(advanced[-1]["t"]+86400+3600,timezone.utc)
        result,state=inc.build(later,{"BTCUSD":advanced},report,state)
        self.assertEqual(len(result["new_history"]),1)
        self.assertEqual(result["assets"]["BTCUSD"]["observations"],1)
        again,state=inc.build(later,{"BTCUSD":advanced},report,state)
        self.assertEqual(again["new_history"],[])
        self.assertEqual(again["assets"]["BTCUSD"]["observations"],1)

    def test_missing_live_observations_retire_and_seed_new_version(self):
        bars,now,report=fixture()
        _,state=inc.build(now,{"BTCUSD":bars},report,{})
        future=bars+[{"t":bars[-1]["t"]+86400,"open":143,"close":144},
                     {"t":bars[-1]["t"]+172800,"open":144,"close":145}]
        later=datetime.fromtimestamp(future[-1]["t"]+86400+3600,timezone.utc)
        result,state=inc.build(later,{"BTCUSD":future},report,state)
        self.assertEqual(result["assets"]["BTCUSD"]["version"],2)
        self.assertEqual(result["assets"]["BTCUSD"]["observations"],0)
        self.assertEqual(len(state["retired"]),1)
        self.assertEqual(result["new_history"],[])

    def test_malicious_parameter_does_not_run(self):
        bars,now,report=fixture()
        report["instruments"]["BTCUSD"]["candidate_parameters"]={"window":999,"buffer":.01}
        result,state=inc.build(now,{"BTCUSD":bars},report,{})
        self.assertEqual(result["assets"],{})
        self.assertIn("BTCUSD",result["errors"])

if __name__=="__main__":unittest.main()
