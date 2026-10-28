"""Regressions for Seiko Lab 04 static dashboard assembly."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class MobileDashboardTests(unittest.TestCase):
 def test_four_module_files_linked(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  for name in ("lab04-core","lab04-home","lab04-directory","lab04-analysis"):
   self.assertIn(name+".js?v=4",html)
   self.assertTrue((ROOT/"site"/(name+".js")).exists())
  for name in ("lab04-overview","lab04-analysis","lab04-markets"):
   self.assertIn(name+".css?v=4",html)
   self.assertTrue((ROOT/"site"/(name+".css")).exists())
 def test_two_portfolios_are_visible_and_separate(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  self.assertIn('data-lab="crypto"',html)
  self.assertIn('data-lab="multi"',html)
  self.assertIn('data-robot-lab="all"',html)
  self.assertIn('id="multi-analysis-chart"',html)
  self.assertIn('id="cross-scorecard"',html)
  self.assertIn('id="market-grid"',html)
  self.assertNotIn('id="export-current"',html)
 def test_market_data_not_counted_as_crypto(self):
  script=(ROOT/"site/lab04-core.js").read_text(encoding="utf8")
  self.assertIn("crypto:cr.length*20",script)
  self.assertIn("r.initial_usd||20",script)
  self.assertNotIn("r.initial_usd||1000",script)
  self.assertIn("history={crypto:",script)
 def test_safe_daily_research_is_integrated(self):
  template=(ROOT/"site/index.html").read_text(encoding="utf8")
  builder=(ROOT/"build_site.py").read_text(encoding="utf8")
  self.assertIn('id="research-title"',template)
  self.assertIn('id="research-idea-list"',template)
  self.assertIn('lab04-research.js?v=4.3',template)
  self.assertIn('data["research"]',builder)
  self.assertIn('id="ai-review-panel"',template)
  self.assertIn('id="ai-experiment-list"',template)
  self.assertIn('data["ai_review"]',builder)
  reviewer=(ROOT/"site/lab04-research.js").read_text(encoding="utf8")
  self.assertIn("aiReview.experiments",reviewer)
  self.assertIn("textContent",reviewer)
  self.assertTrue((ROOT/"site/lab04-research.js").exists())

 def test_workflow_publishes_versions(self):
  workflow=(ROOT/".github/workflows/simulate.yml").read_text(encoding="utf8")
  self.assertIn("cp site/lab04-*.js docs/",workflow)
  self.assertIn("cp site/lab04-*.css docs/",workflow)

if __name__=="__main__":
 unittest.main()
