import unittest
from datetime import datetime, timezone
from research.autonomous_paper_roster import build

def robots():
    return {"schema":1,"real_orders":False,"robots":[
        {"strategy":f"hold{i}","role":"immutable_hold_benchmark","paper_return_pct":-10}
        for i in range(12)]+[
        {"strategy":f"bot{i}","role":"tunable_paper_robot","paper_return_pct":-60}
        for i in range(24)]}

def competition(stage="paper_champion"):
    return {"schema":1,"real_orders":False,"robots_modified":False,"ranked":[{
        "id":"gemini_1","stage":stage,"history_checks_pass":True,"real_orders":False,
        "observed_days":130,"closed_trades":20,"consecutive_qualified_days":14,
        "net_pct":4,"excess_vs_hold_points":3,"drawdown_pct":5}]}

class RosterTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,11,tzinfo=timezone.utc)
    def test_qualifying_paper_champion_joins_independent_roster(self):
        result,state=build(self.now,robots(),competition(),{})
        self.assertEqual(result["active_candidate_ids"],["gemini_1"])
        self.assertEqual(len(result["historical_robots"]),36)
        self.assertFalse(result["legacy_robots_modified"])
        self.assertFalse(result["real_orders"])
    def test_revokes_when_prospective_evidence_decays(self):
        result,_=build(self.now,robots(),competition("paper_champion_revoked"),
                       {"active":["gemini_1"],"events":[]})
        self.assertEqual(result["active_candidate_ids"],[])
        self.assertEqual(result["archived_candidates"][0]["action"],"paper_candidate_revoked")
    def test_never_activates_unqualified_candidate(self):
        c=competition()
        c["ranked"][0]["consecutive_qualified_days"]=0
        result,_=build(self.now,robots(),c,{})
        self.assertEqual(result["active_candidate_count"],0)
    def test_fail_closed_on_modified_hold(self):
        r=robots()
        r["robots"][0]["role"]="tunable_paper_robot"
        with self.assertRaises(ValueError):
            build(self.now,r,competition(),{})

if __name__=="__main__":
    unittest.main()
