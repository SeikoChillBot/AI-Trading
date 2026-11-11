"""Guard the read-only retirement review from accidental auto-archive."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class RetirementReviewContract(unittest.TestCase):
    def test_dashboard_review_is_read_only_and_excludes_hold(self):
        script = (ROOT / "site/lab04-research.js").read_text(encoding="utf-8")
        self.assertIn("item.role!=='immutable_hold_benchmark'", script)
        self.assertIn("Number(item.paper_return_pct)<=-30", script)
        self.assertIn("Number(item.drawdown_pct)>=30", script)
        self.assertIn("Number(item.closed_roundtrips)>=20", script)
        self.assertIn("Aucun robot n’est archivé ou remplacé automatiquement", script)
        self.assertIn("preuve prospective insuffisante", script)

if __name__ == "__main__":
    unittest.main()
