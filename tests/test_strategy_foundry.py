"""Offline tests of cumulative AIT strategy research; zero API or live orders."""
import math
import unittest
from datetime import datetime, timezone, timedelta
from research import strategy_foundry as foundry
from research.ai_decision_support import validate_model_ideas

NOW = datetime(2026, 10, 29, 19, 0, tzinfo=timezone.utc)
FIRST = int((NOW - timedelta(days=720)).timestamp())
FIRST -= FIRST % 86400


def bars(count=720):
    # Continuous, entirely completed historical daily candles.
    values = []
    for i in range(count):
        price = 100 + (i % 23) * .45 + 4 * math.sin(i / 8)
        values.append({"t": FIRST + i * 86400, "open": price,
                       "close": price + .3 * math.sin(i)})
    return values


def idea(logic="trend_following", asset="BTCUSD"):
    return {"asset": asset, "logic": logic, "lookback_days": 20,
            "threshold_pct": 1, "max_hold_days": 3,
            "rationale": "Tester un mécanisme de marché explicite, puis essayer de le falsifier."}


class FoundryTests(unittest.TestCase):
    def test_only_finite_structured_strategies_accepted(self):
        self.assertEqual(foundry.normalise(idea())["max_hold_days"], 3)
        for modified in (
            {**idea(), "asset": "DOGEUSD"},
            {**idea(), "lookback_days": 99999},
            {**idea(), "logic": "import os; os.system('rm -rf /')"},
            {**idea(), "threshold_pct": float("nan")},
            {**idea(), "max_hold_days": -1},
        ):
            with self.assertRaises(ValueError):
                foundry.normalise(modified)

    def test_previous_close_cannot_see_the_future(self):
        spec = foundry.normalise(idea("mean_reversion"))
        sample = bars()
        baseline = foundry.replay(sample, spec, 360, 420)
        # The upcoming period must not affect an earlier fold.
        changed = [dict(x) for x in sample]
        changed[420]["open"] = changed[420]["close"] = 1_000_000
        self.assertEqual(baseline, foundry.replay(changed, spec, 360, 420))
        # Decision on opening at index 420 must ignore current candle close.
        closes = [float(x["close"]) for x in sample]
        signal = foundry.signal(closes, 420, spec, False, 0)
        closes[420] = 1e40
        self.assertEqual(signal, foundry.signal(closes, 420, spec, False, 0))

    def test_exploratory_stress_and_no_promotion(self):
        result = foundry.evaluate(bars(), foundry.normalise(idea()), NOW)
        self.assertEqual(len(result["folds"]), 6)
        self.assertIn("double_cost_net_pct", result["folds"][0])
        self.assertEqual(result["evidence_kind"], "exploratory_historical_replay_not_blind_oos")
        self.assertFalse(result["qualified_for_live_trading"])
        self.assertFalse(result["qualified_for_robot_promotion"])

    def test_no_fake_replay_on_gaps_or_future_prices(self):
        sample = bars()
        sample[30]["t"] += 86400
        with self.assertRaises(ValueError):
            foundry.evaluate(sample, foundry.normalise(idea()), NOW)
        future = bars()
        future[-1]["t"] = int(NOW.timestamp()) + 86400
        with self.assertRaises(ValueError):
            foundry.evaluate(future, foundry.normalise(idea()), NOW)

    def test_memory_is_persistent_deduplicated_and_honest(self):
        inputs = {"BTCUSD": bars(), "ETHUSD": bars(), "SOLUSD": bars()}
        first, status = foundry.build(NOW, {"source": "gemini_generate_content",
            "state": "model_reflection_completed", "strategy_designs": [
                idea("mean_reversion"), idea("mean_reversion")]},
            inputs, {})
        self.assertEqual(len(first["ideas"]), 4)  # 1 Gemini + 3 fixed references
        self.assertEqual(status["gemini_hypotheses"], 1)
        self.assertEqual(status["tested_historically"], 4)
        self.assertFalse(first["promotions_enabled"])
        later, repeat = foundry.build(NOW + timedelta(minutes=20),
            {"source": "gemini_generate_content", "state": "model_reflection_completed",
             "strategy_designs": [idea("mean_reversion")]}, inputs, first)
        self.assertEqual(len(later["ideas"]), 4)
        self.assertEqual([x["review_count"] for x in later["ideas"]], [1] * 4)
        self.assertFalse(any(x["status"] == "exploratory_replay_completed"
                             for x in repeat["events"]))
        memory = foundry.model_memory(later)
        self.assertEqual(len(memory["prior_ideas"]), 4)
        self.assertNotIn("rationale", str(memory))
        self.assertNotIn("wallet", str(memory))
        self.assertFalse(repeat["no_live_trades"] is False)

    def test_unauthenticated_model_proposal_is_not_adopted(self):
        data = {"BTCUSD": bars(), "ETHUSD": bars(), "SOLUSD": bars()}
        ledger, report = foundry.build(NOW, {
            "source": "deterministic_fallback", "state": "model_reflection_failed",
            "strategy_designs": [idea("mean_reversion")]}, data, {})
        self.assertEqual(report["gemini_hypotheses"], 0)
        self.assertEqual(len(ledger["ideas"]), 3)

    def test_model_validation_blocks_code_and_duplicates(self):
        model = {"summary": "Recherche structurée sur signaux de marché",
                 "experiments": [], "bot_adjustments": [],
                 "strategy_designs": [idea(), idea()]}
        valid = validate_model_ideas(model, {})
        self.assertEqual(len(valid["strategy_designs"]), 1)
        model["strategy_designs"] = [{**idea(), "logic": "exec"}]
        with self.assertRaises(ValueError):
            validate_model_ideas(model, {})
        model["strategy_designs"] = [idea(), idea(), idea()]
        with self.assertRaises(ValueError):
            validate_model_ideas(model, {})


if __name__ == "__main__":
    unittest.main()
