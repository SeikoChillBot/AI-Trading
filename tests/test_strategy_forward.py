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

    def test_capacity_rotation_archives_old_trials_and_preserves_paper_champion(self):
        values = candles()
        specs = []
        for logic in foundry.LOGICS:
            for w in (10, 20, 40):
                for threshold in (0.5, 1, 2):
                    candidate = foundry.normalise({
                        "asset": "BTCUSD", "logic": logic,
                        "lookback_days": w, "threshold_pct": threshold,
                        "max_hold_days": 3,
                        "rationale": "Tester la rotation de capacité sans perdre les anciens essais.",
                    })
                    specs.append({"id": foundry.identifier(candidate),
                                  "spec": candidate, "source": "bounded_evolution"})
        first, state = shadow.build(NOW, {"ideas": specs[:24]},
                                    {"BTCUSD": values}, {})
        self.assertEqual(first["tracked"], 24)
        champion = specs[0]["id"]
        league = {"schema": 1, "real_orders": False, "robots_modified": False,
                  "ranked": [{"id": champion, "stage": "paper_champion"}]}
        next_result, state = shadow.build(NOW + timedelta(minutes=15),
            {"ideas": specs[:26]}, {"BTCUSD": values}, state, league)
        self.assertEqual(next_result["tracked"], 24)
        self.assertEqual(next_result["archived_trials"], 2)
        self.assertIn(champion, state["tracks"])
        self.assertIn(specs[25]["id"], state["tracks"])
        self.assertTrue(all(r["status"] == "archived_capacity_rotation"
                            for r in state["archived"]))
        self.assertFalse(next_result["real_orders"])

    def test_never_accepts_or_executes_external_model_code(self):
        compromised = proposal()
        compromised["spec"]["logic"] = "exec"
        result, state = shadow.build(NOW, {"ideas":[compromised]},
                                      {"BTCUSD":candles()}, {})
        self.assertEqual(result["tracked"], 0)
        self.assertEqual(state["tracks"], {})


if __name__ == "__main__":
    unittest.main()
