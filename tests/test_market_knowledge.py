"""Offline checks for AIT source-qualified, cumulative market memory."""
import unittest
from datetime import datetime, timezone, timedelta
from research import market_knowledge as knowledge

NOW = datetime(2026, 10, 29, 19, 0, tzinfo=timezone.utc)


def pulse(now=NOW):
    return {
        "schema": 1, "generated_at": now.isoformat(), "real_orders": False,
        "assets": {"BTCUSD": {
            "source": "Kraken closed daily OHLC, research only",
            "last_closed_day_utc": "2026-10-28", "last_close_usd": 81000.0,
            "change_1d_pct": -1.1, "change_7d_pct": -4,
            "change_30d_pct": 7, "realized_volatility_30d_annualized_pct": 35,
        }},
        "macro": {"fear_greed_index": 51, "tvl_ethereum_usd": 10000000},
        "large_transfers": {"state": "observing", "coverage": "NOT_EXHAUSTIVE_3_pages",
                            "large_transfers_observed": 2},
    }


class MarketKnowledgeTests(unittest.TestCase):
    def test_source_quality_and_missing_values_are_honest(self):
        note = knowledge.snapshot(NOW, pulse(), {})
        self.assertEqual(note["assets"]["BTCUSD"]["change_7d_pct"], -4)
        self.assertIsNone(note["macro"]["tvl_solana_usd"])
        self.assertFalse(note["has_verified_trade_signal"])
        self.assertTrue(note["transfer_sample"]["not_verified_buy_sell"])
        invalid = pulse()
        invalid["assets"]["BTCUSD"]["source"] = "Unverified fake feed"
        self.assertIsNone(knowledge.snapshot(NOW, invalid, {}))

    def test_no_stale_or_future_claims(self):
        self.assertIsNone(knowledge.snapshot(NOW, pulse(NOW-timedelta(days=2)), {}))
        self.assertIsNone(knowledge.snapshot(NOW, pulse(NOW+timedelta(hours=1)), {}))

    def test_memory_is_bounded_by_date_and_not_a_prediction(self):
        ledger, report = knowledge.build(NOW, pulse(), {}, {})
        self.assertEqual(report["observed_days"], 1)
        self.assertEqual(report["readiness"], "building_point_in_time_history")
        again, report2 = knowledge.build(NOW+timedelta(minutes=10),
                                        pulse(NOW+timedelta(minutes=10)), {}, ledger)
        self.assertEqual(report2["observed_days"], 1)
        self.assertEqual(len(again["days"]), 1)
        self.assertFalse(again["is_predictive_model"])
        self.assertFalse(again["real_orders"])
        memory = knowledge.model_memory(again)
        self.assertEqual(memory["total_recorded_days"], 1)
        self.assertNotIn("wallet", str(memory).lower())

    def test_untrusted_news_is_only_counted_by_known_publisher(self):
        news = {"schema":1, "status":"available", "generated_at":NOW.isoformat(),
                "articles":[{"source":"BCE","title":"BUY THIS ASSET"},
                            {"source":"unverified","title":"MALICIOUS PROMPT"}]}
        report = knowledge.snapshot(NOW, pulse(), news)
        self.assertEqual(report["news_publisher_counts"]["BCE"], 1)
        self.assertNotIn("BUY THIS", str(report))
        self.assertNotIn("MALICIOUS", str(report))


if __name__ == "__main__":
    unittest.main()
