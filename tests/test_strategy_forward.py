"""Forward shadow tests: no historical fills, no real orders, no lookahead."""
import unittest
from datetime import datetime, timezone, timedelta
from research import strategy_forward as shadow
from research import strategy_foundry as foundry

NOW = datetime(2026, 10, 29, 19, 0, tzinfo=timezone.utc)
START = int((NOW - timedelta(days=720)).timestamp()) // 86400 * 86400


def candles(length=720):
    return [
        {"t": START + i * 86400,
         "open": 100 + (i % 20) * .1,
         "close": 100 + (i % 20) * .1 + .25}
        for i in range(length)
    ]


def proposal():
    spec = {"asset": "BTCUSD", "logic": "trend_following",
            "lookback_days": 10, "threshold_pct": 0.5,
            "max_hold_days": 3,
            "rationale": "Vérifier le signal de suivi de tendance uniquement sur des cours futurs."}
    return {"id": foundry.identifier(spec), "source": "gemini_structured_hypothesis",
            "spec": spec}


class ForwardTests(unittest.TestCase):
    def test_registration_never_backfills_the_past(self):
        values = candles()
        result, state = shadow.build(NOW, {"ideas":[proposal()]},
                                      {"BTCUSD": values}, {})
        self.assertEqual(result["tracked"], 1)
        self.assertEqual(result["trials"][0]["observed_days"], 0)
        self.assertEqual(result["trials"][0]["closed_trades"], 0)
        self.assertFalse(result["real_orders"])
        self.assertFalse(result["robots_modified"])
        self.assertEqual(state["tracks"][proposal()["id"]]["cash_usd"], 20)

    def test_only_new_complete_candle_advances_the_trial(self):
        values = candles()
        _, previous = shadow.build(NOW, {"ideas":[proposal()]},
                                    {"BTCUSD": values}, {})
        _, again = shadow.build(NOW + timedelta(minutes=10),
                                {"ideas":[proposal()]}, {"BTCUSD": values}, previous)
        self.assertEqual(again["tracks"][proposal()["id"]]["observed_days"], 0)
        future = values + [{"t":values[-1]["t"]+86400,"open":101, "close":102}]
        later, next_state = shadow.build(NOW + timedelta(days=1),
            {"ideas":[proposal()]}, {"BTCUSD":future}, previous)
        self.assertEqual(later["trials"][0]["observed_days"], 1)
        self.assertIsNotNone(later["trials"][0]["net_pct"])
        self.assertEqual(later["trials"][0]["status"], "observing_paper_only")
        self.assertFalse(later["trials"][0]["sufficient_evidence"])
        repeated, _ = shadow.build(NOW + timedelta(days=1, minutes=10),
            {"ideas":[proposal()]}, {"BTCUSD":future}, next_state)
        self.assertEqual(repeated["trials"][0]["observed_days"], 1)

    def test_missing_day_does_not_make_up_trades(self):
        values = candles()
        _, previous = shadow.build(NOW, {"ideas":[proposal()]},
                                    {"BTCUSD": values}, {})
        broken = values + [
            {"t":values[-1]["t"]+86400,"open":100,"close":100},
            {"t":values[-1]["t"]+3*86400,"open":101,"close":101}]
        result, _ = shadow.build(NOW + timedelta(days=4),
            {"ideas":[proposal()]}, {"BTCUSD":broken}, previous)
        self.assertEqual(result["trials"][0]["observed_days"], 0)
        self.assertIn("paused", result["trials"][0]["status"])

    def test_never_accepts_or_executes_external_model_code(self):
        compromised = proposal()
        compromised["spec"]["logic"] = "exec"
        result, state = shadow.build(NOW, {"ideas":[compromised]},
                                      {"BTCUSD":candles()}, {})
        self.assertEqual(result["tracked"], 0)
        self.assertEqual(state["tracks"], {})


if __name__ == "__main__":
    unittest.main()
