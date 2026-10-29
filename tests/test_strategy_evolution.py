"""No-lookahead and paper-only tests for evolving strategies."""
import math
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from research import strategy_foundry as foundry
from research import strategy_evolution as evolve
from research import autonomous_optimizer as optimizer

NOW = datetime(2026, 10, 29, 19, tzinfo=timezone.utc)
START = int(NOW.timestamp()) // 86400 * 86400 - 720 * 86400


def bars():
    return [
        {"t": START + i * 86400,
         "open": 100 + 0.4 * i / 10 + 6 * math.sin(i / 15),
         "close": 100 + 0.4 * (i+1) / 10 + 6 * math.sin((i+1) / 15)}
        for i in range(720)
    ]


def spec(logic):
    return foundry.normalise({
        "asset": "BTCUSD", "logic": logic, "lookback_days": 20,
        "threshold_pct": 1, "max_hold_days": 3,
        "rationale": "Comparer honnêtement les règles de prix au témoin fictif.",
    })


class EvolutionTests(unittest.TestCase):
    def test_all_indicator_signals_observe_only_previous_closes(self):
        values = [float(b["close"]) for b in bars()]
        for logic in foundry.LOGICS:
            s = spec(logic)
            at = foundry.signal(values, 120, s, False, 0)
            poisoned = list(values)
            poisoned[120] *= 1000
            poisoned[121:] = [1] * len(poisoned[121:])
            self.assertEqual(at, foundry.signal(poisoned, 120, s, False, 0), logic)
            self.assertIn(at, ("BUY", "WAIT"))
            result = foundry.replay(bars(), s, 420, 480)
            self.assertTrue(math.isfinite(result["net_pct"]))

    def test_composed_signals_are_canonical_and_have_no_future_leakage(self):
        basic = spec("ema_trend")
        decorated = foundry.normalise({**basic,
            "confirmations": ["positive_momentum", "rsi_strength"]})
        permuted = foundry.normalise({**basic,
            "confirmations": ["rsi_strength", "positive_momentum"]})
        self.assertEqual(foundry.identifier(decorated), foundry.identifier(permuted))
        self.assertNotEqual(foundry.identifier(basic), foundry.identifier(decorated))
        self.assertNotIn("confirmations", foundry.normalise(basic))
        values = [float(b["close"]) for b in bars()]
        for i in (95, 150, 700):
            original = foundry.signal(values, i, decorated, False, 0)
            changed = list(values)
            changed[i:] = [v * 10 for v in changed[i:]]
            self.assertEqual(original, foundry.signal(changed, i, decorated, False, 0))
        result = foundry.replay(bars(), decorated, 450, 510)
        self.assertTrue(math.isfinite(result["net_pct"]))
        self.assertIn(result["closed_trades"], range(0, 70))

    def test_invalid_generated_code_remains_rejected(self):
        with self.assertRaises(ValueError):
            foundry.normalise({**spec("ema_trend"), "logic": "__import__('os')"})
        variants = list(evolve.mutations(spec("ema_trend")))
        self.assertGreater(len(variants), len(foundry.LOGICS)-1+2+2+2)
        self.assertTrue(any(v.get("confirmations") for _, v in variants))
        for bad_gates in (["quiet_volatility", "active_volatility"],
                          ["rsi_oversold", "rsi_strength"],
                          ["unknown_indicator"]):
            with self.assertRaises(ValueError):
                foundry.normalise({**spec("ema_trend"), "confirmations":bad_gates})

    def test_mutation_is_recorded_and_never_claims_profit(self):
        candles = {a:bars() for a in foundry.ASSETS}
        def restricted(asset):
            for logic in ("trend_following", "mean_reversion", "breakout"):
                yield foundry.normalise({**spec(logic), "asset":asset})
        with patch.object(optimizer, "grid", restricted):
            opt, _ = optimizer.build(NOW, candles, {})
        report, state = evolve.build(NOW, candles, opt, {}, {"ideas":[]})
        self.assertGreaterEqual(report["total_mutations"], 3)
        self.assertEqual(len(report["new_candidate_ids"]), report["total_mutations"])
        self.assertEqual(len(report["composed_by_asset"]), 3)
        self.assertTrue(any(x["spec"].get("confirmations") for x in report["candidates"]))
        self.assertEqual(len(report["selected_by_asset"]), 3)
        self.assertFalse(report["real_orders"])
        for item in report["candidates"]:
            self.assertEqual(item["parent_failure_reasons"],
                             evolve.failure_diagnosis(next(x for x in opt["candidates"]
                                                       if x["id"] == item["parent_id"])))
            self.assertTrue(item["historical_candidate_only"])
            self.assertFalse(item["eligible_for_live_trading"])
        repeat, next_state = evolve.build(NOW + timedelta(minutes=10),
                                           candles, opt, state, {"ideas":[]})
        self.assertEqual(repeat["new_candidate_ids"], [])
        self.assertEqual(state["selected_by_asset"], next_state["selected_by_asset"])

    def test_foundry_archives_evolution_separately_from_gemini(self):
        candles = {a:bars() for a in foundry.ASSETS}
        def restricted(asset):
            for logic in ("trend_following", "mean_reversion", "breakout"):
                yield foundry.normalise({**spec(logic), "asset":asset})
        with patch.object(optimizer, "grid", restricted):
            opt, _ = optimizer.build(NOW, candles, {})
        evolution, _ = evolve.build(NOW, candles, opt, {}, {})
        registry, report = foundry.build(NOW, {}, candles, {}, opt, evolution)
        self.assertGreaterEqual(report["evolved_hypotheses"], 3)
        self.assertTrue(any(x["spec"].get("confirmations") for x in registry["ideas"]))
        self.assertEqual(report["gemini_hypotheses"], 0)
        self.assertFalse(registry["promotions_enabled"])
        tampered = {**evolution, "real_orders":True}
        _, rejected = foundry.build(NOW, {}, candles, {}, opt, tampered)
        self.assertEqual(rejected["evolved_hypotheses"], 0)


if __name__ == "__main__":
    unittest.main()
