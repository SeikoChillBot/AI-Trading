"""Independent evidence-bound crossover research regressions."""
import math
import unittest
from datetime import datetime, timezone, timedelta

from research import strategy_architect as architect
from research import strategy_foundry as foundry

NOW = datetime(2026, 10, 29, 19, tzinfo=timezone.utc)
START = int(NOW.timestamp()) // 86400 * 86400 - 720 * 86400


def bars():
    return [
        {"t": START + i * 86400,
         "open": 100 + i / 20 + 5 * math.sin(i / 13),
         "close": 100 + (i + 1) / 20 + 5 * math.sin((i+1) / 13)}
        for i in range(720)
    ]


def memory():
    items = []
    for asset in foundry.ASSETS:
        for logic, w in (("trend_following", 10), ("mean_reversion", 20)):
            spec = foundry.normalise({
                "asset": asset, "logic": logic,
                "lookback_days": w, "threshold_pct": 1, "max_hold_days": 3,
                "rationale": "Hypothèse contrôlée avec des signaux de marché figés.",
            })
            items.append({"id": foundry.identifier(spec), "spec": spec,
                          "source": "deterministic_reference",
                          "latest_result": {"historical_only": True}})
    return {"ideas": items, "real_orders": False}


class ArchitectTests(unittest.TestCase):
    def test_crossover_generates_two_distinct_composite_ideas_per_asset(self):
        market = {asset: bars() for asset in foundry.ASSETS}
        report, state = architect.build(NOW, market, memory(), {})
        self.assertEqual(len(report["new_candidate_ids"]), 6)
        self.assertEqual(len(report["selected_by_asset"]), 3)
        self.assertEqual(report["archived_candidates"], 6)
        self.assertEqual(len(report["observed_price_regimes"]), 3)
        self.assertFalse(report["real_orders"])
        for row in report["candidates"]:
            self.assertEqual(len(row["parent_ids"]), 2)
            self.assertEqual(len(row["spec"]["confirmations"]), 2)
            self.assertEqual(row["source"], "autonomous_crossover")
            self.assertTrue(row["historical_candidate_only"])
            self.assertFalse(row["eligible_for_live_trading"])
            self.assertTrue(row["historical_challenge"]["period"].endswith("not_pristine_oos"))
        later, state2 = architect.build(NOW + timedelta(minutes=20), market, memory(), state)
        self.assertEqual(later["new_candidate_ids"], [])
        self.assertEqual(state["selected_by_asset"], state2["selected_by_asset"])

    def test_last_historical_challenge_never_selects_winner(self):
        market = {asset: bars() for asset in foundry.ASSETS}
        first, _ = architect.build(NOW, market, memory(), {})
        altered = {asset: [dict(bar) for bar in bars()] for asset in foundry.ASSETS}
        for index, item in enumerate(altered["BTCUSD"][-120:]):
            # Changing the slope rather than scaling every price identically
            # changes trailing returns while leaving development folds intact.
            item["open"] *= (1 + index / 300)
            item["close"] *= (1 + index / 300)
        second, _ = architect.build(NOW, altered, memory(), {})
        self.assertEqual(first["selected_by_asset"]["BTCUSD"],
                         second["selected_by_asset"]["BTCUSD"])
        self.assertNotEqual(
            first["observed_price_regimes"]["BTCUSD"],
            second["observed_price_regimes"]["BTCUSD"])

    def test_foundry_keeps_crossover_outside_gemini_and_executing_robots(self):
        market = {asset: bars() for asset in foundry.ASSETS}
        blueprint, _ = architect.build(NOW, market, memory(), {})
        ledger, report = foundry.build(NOW, {}, market, {}, None, None, blueprint)
        self.assertEqual(report["crossed_hypotheses"], 6)
        self.assertEqual(report["gemini_hypotheses"], 0)
        self.assertFalse(ledger["real_orders"])
        self.assertFalse(ledger["promotions_enabled"])
        forged = dict(blueprint, real_orders=True)
        _, rejected = foundry.build(NOW, {}, market, {}, None, None, forged)
        self.assertEqual(rejected["crossed_hypotheses"], 0)

    def test_missing_verified_parent_is_reported_not_fabricated(self):
        market = {asset: bars() for asset in foundry.ASSETS}
        out, state = architect.build(NOW, market, {"ideas":[]}, {})
        self.assertEqual(out["archived_candidates"], 0)
        self.assertEqual(len(out["issues"]), 3)
        self.assertEqual(state["candidates"], [])


if __name__ == "__main__":
    unittest.main()
