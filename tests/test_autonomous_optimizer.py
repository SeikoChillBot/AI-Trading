"""Offline regression tests for independent, finite-grid AIT optimization."""
import math
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from research import autonomous_optimizer as opt
from research import strategy_foundry as foundry

NOW = datetime(2026, 10, 29, 19, 0, tzinfo=timezone.utc)
START = int(NOW.timestamp()) // 86400 * 86400 - 720 * 86400


def prices():
    return [
        {"t": START + i * 86400,
         "open": 100 + math.sin(i / 13) * 5 + i / 100,
         "close": 100 + math.sin((i + 1) / 13) * 5 + i / 100}
        for i in range(720)
    ]


def small_grid(asset):
    for style in ("trend_following", "mean_reversion", "breakout"):
        yield foundry.normalise({
            "asset": asset, "logic": style, "lookback_days": 20,
            "threshold_pct": 1, "max_hold_days": 3,
            "rationale": "Tester automatiquement cette hypothèse séparément des robots.",
        })


class OptimizerTests(unittest.TestCase):
    def test_selection_ignores_future_historical_challenge_prices(self):
        data = prices()
        with patch.object(opt, "grid", small_grid):
            first = opt.optimise_asset(data, "BTCUSD", NOW)
            revised = [dict(x) for x in data]
            for item in revised[-120:]:
                item["open"] *= 1.25
                item["close"] *= .8
            changed = opt.optimise_asset(revised, "BTCUSD", NOW)
        self.assertEqual(first["id"], changed["id"])
        self.assertEqual(first["selection_metrics"], changed["selection_metrics"])
        self.assertEqual(first["grid_evaluated"], 3)
        self.assertNotEqual(first["historical_challenge"],
                            changed["historical_challenge"])
        self.assertFalse(first["eligible_for_live_trading"])

    def test_automatic_search_is_idempotent_and_weekly(self):
        dataset = {s: prices() for s in foundry.ASSETS}
        with patch.object(opt, "grid", small_grid):
            first, state = opt.build(NOW, dataset, {})
            again, state2 = opt.build(NOW + timedelta(minutes=12), dataset, state)
            # A week later on the exact same candle is still not a new search.
            third, _ = opt.build(NOW + timedelta(days=1), dataset, state2)
        self.assertEqual(len(first["new_candidate_ids"]), 3)
        self.assertEqual(len(again["new_candidate_ids"]), 0)
        self.assertEqual(len(third["new_candidate_ids"]), 0)
        self.assertEqual(first["candidate_count"], 3)
        self.assertEqual(again["candidate_count"], 3)
        self.assertEqual(again["latest_by_asset"], first["latest_by_asset"])
        self.assertFalse(first["real_orders"])
        self.assertFalse(first["robot_changes"])

    def test_invalid_sources_do_not_invent_a_candidate(self):
        bad = prices()
        bad[120]["t"] = bad[119]["t"]
        with patch.object(opt, "grid", small_grid):
            report, state = opt.build(NOW, {"BTCUSD": bad}, {})
        self.assertEqual(report["candidate_count"], 0)
        self.assertIn("BTCUSD", report["issues"])
        self.assertEqual(state["candidates"], [])

    def test_foundry_accepts_only_authentic_paper_optimizer_provenance(self):
        dataset = {s: prices() for s in foundry.ASSETS}
        with patch.object(opt, "grid", small_grid):
            response, _ = opt.build(NOW, dataset, {})
        saved, report = foundry.build(NOW, {}, dataset, {}, response)
        self.assertEqual(report["auto_optimized_hypotheses"], 3)
        self.assertTrue(all(item["latest_result"]["qualified_for_live_trading"] is False
                            for item in saved["ideas"]))
        # A forged candidate cannot bypass the local finite strategy grammar.
        compromised = dict(response)
        compromised["real_orders"] = True
        _, rejected = foundry.build(NOW, {}, dataset, {}, compromised)
        self.assertEqual(rejected["auto_optimized_hypotheses"], 0)
        compromised = dict(response)
        compromised["candidates"] = [
            {**response["candidates"][0],
             "spec": {**response["candidates"][0]["spec"], "logic": "__import__"}}
        ]
        _, rejected = foundry.build(NOW, {}, dataset, {}, compromised)
        self.assertLess(rejected["auto_optimized_hypotheses"], 3)

    def test_optimizer_does_not_claim_historical_fit_is_proof(self):
        with patch.object(opt, "grid", small_grid):
            candidate = opt.optimise_asset(prices(), "SOLUSD", NOW)
        self.assertEqual(
            candidate["historical_challenge"]["period"],
            "reused_historical_challenge_not_pristine_oos")
        self.assertTrue(candidate["prospective_data_required"])
        self.assertNotIn("live_orders", candidate)


if __name__ == "__main__":
    unittest.main()
