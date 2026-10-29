"""AIT cumulative scientific memory: idempotence, provenance and long-term failures."""
import unittest
from datetime import datetime, timezone, timedelta

from research import scientific_memory as science
from research import strategy_foundry as foundry

NOW = datetime(2026, 10, 29, 22, tzinfo=timezone.utc)


def knowledge(digest="a"*64):
    spec = foundry.normalise({
        "asset": "BTCUSD", "logic": "dual_confirmation",
        "lookback_days": 20, "threshold_pct": 1,
        "max_hold_days": 3,
        "confirmations": ["ema_uptrend","rsi_strength"],
        "rationale": "Hypothèse falsifiable pour conserver les échecs après archivage.",
    })
    id_ = foundry.identifier(spec)
    return {
        "schema": 1, "real_orders": False, "never_run_model_code": True,
        "promotions_enabled": False,
        "ideas": [{
            "id": id_, "source": "autonomous_crossover",
            "spec": spec, "latest_data_sha256": digest,
            "latest_result": {
                "average_net_pct": -2.0, "average_double_cost_net_pct": -4.0,
                "average_excess_vs_hold_points": -5.0, "max_drawdown_pct": 7.0,
                "checks": {
                    "positive_average_net": False,
                    "positive_with_double_costs": False,
                    "beats_hold_in_most_folds": False,
                    "drawdown_under_20_pct": True,
                },
            },
        }],
    }


class ScienceTests(unittest.TestCase):
    def test_history_revisions_are_deduplicated_by_evidence_hash(self):
        first, state = science.build(NOW, knowledge(), {}, {})
        self.assertEqual(first["recorded_hypotheses"], 1)
        self.assertEqual(first["new_revisions"], 1)
        self.assertEqual(first["prospective_observed"], 0)
        self.assertEqual(first["failure_patterns"]["positive_average_net"], 1)
        again, state2 = science.build(NOW + timedelta(minutes=10), knowledge(), {}, state)
        self.assertEqual(again["new_revisions"], 0)
        self.assertEqual(state2["lessons"][0]["historical_revisions"], 1)
        revised, state3 = science.build(NOW + timedelta(days=1), knowledge("b"*64), {}, state2)
        self.assertEqual(revised["new_revisions"], 1)
        self.assertEqual(state3["lessons"][0]["historical_revisions"], 2)
        self.assertEqual(len(state3["lessons"][0]["historical_snapshots"]), 2)
        self.assertFalse(revised["real_orders"])

    def test_prior_failures_survive_when_idea_is_archived_out_of_working_memory(self):
        _, state = science.build(NOW, knowledge(), {}, {})
        empty = knowledge()
        empty["ideas"] = []
        result, persisted = science.build(NOW + timedelta(days=1), empty, {}, state)
        self.assertEqual(result["recorded_hypotheses"], 1)
        self.assertEqual(result["total_experiment_fingerprints"], 1)
        self.assertEqual(result["new_revisions"], 0)
        self.assertIn("positive_average_net", result["failure_patterns"])
        self.assertFalse(persisted["real_orders"])

    def test_forward_results_only_from_authenticated_future_observations(self):
        k = knowledge()
        id_ = k["ideas"][0]["id"]
        fake = {"schema": 1, "real_orders": False, "tracks": {
            id_: {"id":id_, "status":"observing_paper_only",
                  "observed_days":0, "net_pct":9000}}}
        report, state = science.build(NOW, k, fake, {})
        self.assertEqual(report["prospective_observed"], 0)
        fake["tracks"][id_]["observed_days"] = 1
        fake["tracks"][id_]["net_pct"] = -1.
        real, state = science.build(NOW+timedelta(days=1), k, fake, state)
        self.assertEqual(real["prospective_observed"], 1)
        self.assertEqual(state["lessons"][0]["latest_prospective"]["net_pct"], -1.)
        self.assertFalse(real["no_promotions"] is False)

    def test_rejects_forged_or_unsafe_foundry(self):
        forged = knowledge()
        forged["real_orders"] = True
        result, _ = science.build(NOW, forged, {}, {})
        self.assertEqual(result["state"], "invalid_research_input")
        forged = knowledge()
        forged["ideas"][0]["id"] = "not_a_valid_id"
        result, _ = science.build(NOW, forged, {}, {})
        self.assertEqual(result["recorded_hypotheses"], 0)


if __name__ == "__main__":
    unittest.main()
