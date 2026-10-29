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

    def test_invalid_generated_code_remains_rejected(self):
        with self.assertRaises(ValueError):
            foundry.normalise({**spec("ema_trend"), "logic": "__import__('os')"})
        self.assertEqual(len(list(evolve.mutations(spec("ema_trend")))),
                         len(foundry.LOGICS)-1+2+2+2)

    def test_mutation_is_recorded_and_never_claims_profit(self):
        candles = {a:bars() for a in foundry.ASSETS}
        def restricted(asset):
            for logic in ("trend_following", "mean_reversion", "breakout"):
                yield foundry.normalise({**spec(logic), "asset":asset})
        with patch.object(optimizer, "grid", restricted):
            opt, _ = optimizer.build(NOW, candles, {})
        report, state = evolve.build(NOW, candles, opt, {}, {"ideas":[]})
        self.assertEqual(report["total_mutations"], 3)
        self.assertEqual(len(report["new_candidate_ids"]), 3)
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
        self.assertEqual(report["evolved_hypotheses"], 3)
        self.assertEqual(report["gemini_hypotheses"], 0)
        self.assertFalse(registry["promotions_enabled"])
        tampered = {**evolution, "real_orders":True}
        _, rejected = foundry.build(NOW, {}, candles, {}, opt, tampered)
        self.assertEqual(rejected["evolved_hypotheses"], 0)


if __name__ == "__main__":
    unittest.main()
