"""No real trades, even when a long paper experiment meets review targets."""
import unittest
from datetime import datetime, timezone, timedelta
from research import manual_live_review as gate
from research import strategy_foundry as foundry

NOW = datetime(2026, 10, 29, 19, tzinfo=timezone.utc)


def setup():
    spec = foundry.normalise({
        "asset": "BTCUSD", "logic": "trend_following",
        "lookback_days": 20, "threshold_pct": 1, "max_hold_days": 3,
        "rationale": "Historique fictif à contrôler par une revue humaine seulement.",
    })
    identifier = foundry.identifier(spec)
    passed = {
        "enough_closed_trades": True,
        "positive_average_net": True,
        "positive_with_double_costs": True,
        "beats_hold_in_most_folds": True,
        "drawdown_under_20_pct": True,
    }
    history = {"ideas": [{"id": identifier, "spec": spec,
        "latest_result": {
            "evidence_kind": "exploratory_historical_replay_not_blind_oos",
            "checks": passed}}]}
    forward = {"schema": 1, "generated_at": NOW.isoformat(), "real_orders": False,
               "robots_modified": False,
               "trials": [{
                   "id": identifier, "status": "observing_paper_only",
                   "observed_days": 120, "closed_trades": 15, "net_pct": 8,
                   "excess_vs_hold_points": 2, "max_drawdown_pct": 8,
               }]}
    return forward, history


class ManualReviewTests(unittest.TestCase):
    def test_passing_screen_never_autorizes_real_funds(self):
        forward, knowledge = setup()
        result = gate.build(NOW, forward, knowledge)
        self.assertEqual(result["eligible_for_human_review"], 1)
        self.assertEqual(result["trials"][0]["status"],
                         "eligible_for_human_risk_review_only")
        self.assertFalse(result["trials"][0]["live_approved"])
        self.assertFalse(result["trials"][0]["can_place_real_orders"])
        self.assertFalse(result["real_trading_enabled"])
        self.assertFalse(result["model_can_enable_live_trading"])
        self.assertTrue(result["requires_explicit_user_approval"])

    def test_positive_result_without_history_does_not_pass(self):
        forward, knowledge = setup()
        knowledge["ideas"][0]["latest_result"]["checks"]["positive_with_double_costs"] = False
        result = gate.build(NOW, forward, knowledge)
        self.assertEqual(result["eligible_for_human_review"], 0)
        self.assertIn("historical_stress_checks_not_passed", result["trials"][0]["blockers"])

    def test_short_paper_track_blocks_future_live_review(self):
        forward, knowledge = setup()
        forward["trials"][0]["observed_days"] = 20
        forward["trials"][0]["net_pct"] = -2
        forward["trials"][0]["max_drawdown_pct"] = 25
        result = gate.build(NOW, forward, knowledge)
        self.assertEqual(result["eligible_for_human_review"], 0)
        self.assertGreaterEqual(len(result["trials"][0]["blockers"]), 3)

    def test_unsafe_provenance_prevents_review(self):
        forward, knowledge = setup()
        forward["real_orders"] = True
        report = gate.build(NOW, forward, knowledge)
        self.assertEqual(report["tracked_research_candidates"], 0)
        self.assertEqual(report["eligible_for_human_review"], 0)


if __name__ == "__main__":
    unittest.main()
