"""Static multi-market catalog safety and publication checks."""
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/market_catalog.json"


class MarketCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.markets = cls.catalog["markets"]

    def test_has_diverse_markets_and_valid_schema(self):
        self.assertEqual(self.catalog["schema_version"], 1)
        self.assertGreaterEqual(len(self.markets), 10)
        self.assertGreaterEqual(len({x["family"] for x in self.markets}), 7)
        ids = [x["id"] for x in self.markets]
        self.assertEqual(len(ids), len(set(ids)))

    def test_only_crypto_is_live_in_a_paper_simulation(self):
        active = [m["id"] for m in self.markets if m["status"] == "active"]
        self.assertEqual(active, ["crypto"])
        self.assertEqual(self.catalog["risk_policy"], "paper_only_no_leverage_no_real_orders")

    def test_no_unverified_capital_or_performance_in_research_categories(self):
        forbidden = {"capital_usd", "return_pct", "profit_usd", "balance", "win_rate", "verified_returns"}
        for market in self.markets:
            with self.subTest(market=market["id"]):
                self.assertTrue(forbidden.isdisjoint(market.keys()))
                self.assertIn(market["status"], {"active", "connect", "research", "high_risk"})
                self.assertTrue(market["title"].strip())
                self.assertTrue(market["strategies"])
                self.assertTrue(market["data"])
                self.assertTrue(market["constraint"])
                self.assertTrue(market["source"].startswith("https://"))

    def test_frontend_uses_same_catalog_without_affecting_portfolios(self):
        template = (ROOT/"site/index.html").read_text(encoding="utf-8")
        app = (ROOT/"site/app.js").read_text(encoding="utf-8")
        builder = (ROOT/"build_site.py").read_text(encoding="utf-8")
        self.assertIn('id="view-explore"', template)
        self.assertIn('data-view="explore"', template)
        self.assertIn('id="market-grid"', template)
        self.assertIn("renderMarketExplorer();", app)
        self.assertIn("data['market_catalog'] = catalog", builder)
        self.assertIn("data['fx'] = load_fx()", builder)


if __name__ == "__main__":
    unittest.main()
