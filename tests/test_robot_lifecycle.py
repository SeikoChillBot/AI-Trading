import unittest
from research.robot_lifecycle import evaluate

class LifecycleTests(unittest.TestCase):
    def test_review_does_not_archive_or_promote(self):
        robots=[{"strategy":"bad","role":"tunable_paper_robot","paper_return_pct":-60,
                 "drawdown_pct":61,"closed_roundtrips":40},
                {"strategy":"hold","role":"immutable_hold_benchmark","paper_return_pct":-60,
                 "drawdown_pct":61,"closed_roundtrips":40}]
        forward={"trials":[{"id":"candidate","source":"gemini_structured_hypothesis",
                            "asset":"BTCUSD","logic":"trend_following","observed_days":90,
                            "closed_trades":60,"net_pct":20,"excess_vs_hold_points":15,
                            "max_drawdown_pct":3}]}
        result=evaluate(robots,forward,"2026-11-11T00:00:00+00:00")
        self.assertEqual(result["robots"][0]["decision"],"review_for_retirement")
        self.assertEqual(result["robots"][1]["decision"],"immutable_benchmark")
        self.assertEqual(result["automatic_archivals"],0)
        self.assertEqual(result["automatic_promotions"],0)
        self.assertFalse(result["candidate_trials"][0]["qualified"])
        self.assertFalse(result["candidate_trials"][0]["checks"]["double_fees_resilience"])
        self.assertFalse(result["candidate_trials"][0]["checks"]["paired_market_regimes"])

    def test_missing_evidence_fails_closed(self):
        result=evaluate([{"strategy":"unknown","role":"tunable_paper_robot"}],
                        {"trials":[{"id":"new"}]})
        self.assertEqual(result["robots"][0]["decision"],"continue_observation")
        self.assertFalse(result["candidate_trials"][0]["qualified"])

if __name__=="__main__":
    unittest.main()
