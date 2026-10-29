"""Paper leaderboard safety, new-day idempotence and automatic champion revocation."""
import unittest
from datetime import datetime, timezone, timedelta

from research import strategy_competition as competition
from research import strategy_foundry as foundry

NOW = datetime(2026, 10, 29, 19, tzinfo=timezone.utc)
D = 86400
BASE = int(NOW.timestamp()) - 5 * D


def setup():
    s = foundry.normalise({
        "asset": "BTCUSD", "logic": "ema_trend", "lookback_days": 20,
        "threshold_pct": 1, "max_hold_days": 3,
        "rationale": "Tests de classement papier validé seulement sur les nouveaux jours.",
    })
    key=foundry.identifier(s)
    check={k:True for k in ("enough_closed_trades","positive_average_net",
            "positive_with_double_costs","beats_hold_in_most_folds",
            "drawdown_under_20_pct")}
    knowledge={"schema":1,"real_orders":False,"ideas":[{"id":key,"spec":s,
                  "source":"bounded_evolution","latest_result":{"checks":check}}]}
    forward={"schema":1,"real_orders":False,
             "tracks":{key:{"id":key,"spec":s,"status":"observing_paper_only",
                              "last_t":BASE,"observed_days":120,
                              "closed_trades":13,"net_pct":5,
                              "excess_vs_hold_points":2,"max_drawdown_pct":4}}}
    return key,forward,knowledge


class CompetitionTests(unittest.TestCase):
    def test_no_champion_before_consecutive_fresh_days(self):
        key, forward, knowledge = setup()
        earlier={}
        for i in range(14):
            forward["tracks"][key]["last_t"]=BASE + i * D
            forward["tracks"][key]["observed_days"]=120+i
            report,earlier=competition.build(NOW+timedelta(days=i),forward,knowledge,earlier)
        self.assertEqual(report["paper_champions"],1)
        self.assertEqual(report["ranked"][0]["stage"],"paper_champion")
        repeat,state=competition.build(NOW+timedelta(days=14),forward,knowledge,earlier)
        self.assertEqual(state["trails"][key]["consecutive_qualified_days"],14)
        self.assertEqual(len(state["trails"][key]["daily_snapshots"]),14)
        self.assertFalse(repeat["real_orders"])
        self.assertFalse(repeat["robots_modified"])
        self.assertEqual(repeat["original_robots_promoted"],0)

    def test_champion_loses_status_after_new_drawdown(self):
        key, forward, knowledge = setup()
        state={"trails":{key:{"stage":"paper_champion","last_observed_t":BASE-D,
                              "consecutive_qualified_days":14,"daily_snapshots":[]}}}
        forward["tracks"][key]["max_drawdown_pct"]=22
        report, state=competition.build(NOW,forward,knowledge,state)
        self.assertEqual(report["paper_champions"],0)
        self.assertEqual(report["ranked"][0]["stage"],"paper_champion_revoked")
        self.assertEqual(state["trails"][key]["consecutive_qualified_days"],0)

    def test_no_new_observation_no_champion(self):
        key,forward,knowledge=setup()
        state={"trails":{key:{"last_observed_t":BASE,
                              "consecutive_qualified_days":13,"daily_snapshots":[]}}}
        report, next_state=competition.build(NOW,forward,knowledge,state)
        self.assertEqual(report["paper_champions"],0)
        self.assertEqual(report["ranked"][0]["stage"],"qualifying_paper_candidate")
        self.assertEqual(next_state["trails"][key]["consecutive_qualified_days"],13)

    def test_mismatched_evidence_never_qualifies(self):
        key,forward,knowledge=setup()
        knowledge["ideas"][0]["id"]="forged"
        report,_=competition.build(NOW,forward,knowledge,{})
        self.assertEqual(report["paper_champions"],0)
        self.assertEqual(report["tracked"],0)
        forward["real_orders"]=True
        report,_=competition.build(NOW,forward,knowledge,{})
        self.assertEqual(report["state"],"unavailable")


if __name__=="__main__":
    unittest.main()
