"""Regression tests for bounded Kraken OHLC network recovery."""
import unittest
from unittest.mock import patch, MagicMock
import requests
from bot import fetch_candles


class KrakenRetryTests(unittest.TestCase):
    def test_retry_policy_and_successful_closed_candles(self):
        candle = lambda i: [1700000000 + i * 300, "1", "2", "1", "2", "3", "4", "5"]
        response = MagicMock()
        response.json.return_value = {"error": [], "result": {"XXBTZUSD": [candle(i) for i in range(32)], "last": 1}}
        with patch("requests.Session") as session_cls:
            session = session_cls.return_value.__enter__.return_value
            session.get.return_value = response
            result = fetch_candles("BTCUSDT", 5)
            self.assertEqual(len(result), 31)
            self.assertEqual(result[-1][0], (1700000000 + 30 * 300) * 1000)
            adapter = session.mount.call_args.args[1]
            retries = adapter.max_retries
            self.assertEqual(retries.total, 2)
            self.assertEqual(retries.read, 2)
            self.assertIn(503, retries.status_forcelist)
            self.assertEqual(retries.allowed_methods, frozenset(("GET",)))
            self.assertEqual(session.get.call_args.kwargs["timeout"], (5, 20))

    def test_exhausted_timeout_propagates_without_fake_prices(self):
        with patch("requests.Session") as session_cls:
            session = session_cls.return_value.__enter__.return_value
            session.get.side_effect = requests.exceptions.ReadTimeout("Kraken timeout")
            with self.assertRaises(requests.exceptions.ReadTimeout):
                fetch_candles("BTCUSDT", 5)


if __name__ == "__main__":
    unittest.main()
