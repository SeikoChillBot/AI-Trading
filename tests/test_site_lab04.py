"""Regressions for Seiko Lab 04 static dashboard assembly."""
import unittest
from test_novice_ui import UIChecks  # also exercises the simple site in the existing CI run
from test_ait_explanation import ExplanationTests
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
  self.assertRegex(template, r'lab04-research\.js\?v=4\.\d+')
  self.assertIn('data["research"]',builder)
  self.assertIn('id="ai-review-panel"',template)
  self.assertIn('id="ai-experiment-list"',template)
  self.assertIn('data["ai_review"]',builder)
  self.assertIn('id="market-pulse-panel"',template)
  self.assertIn('id="forward-incubator-panel"',template)
  self.assertIn('data["market_pulse"]',builder)
  self.assertIn('data["forward_challengers"]',builder)
  self.assertIn('id="robot-evolution-panel"',template)
  self.assertIn('id="evolution-bot-list"',template)
  self.assertIn('id="evolution-event-list"',template)
  self.assertIn('data["robot_evolution"]',builder)
  reviewer=(ROOT/"site/lab04-research.js").read_text(encoding="utf8")
  self.assertIn("aiReview.experiments",reviewer)
  self.assertIn("textContent",reviewer)
  self.assertTrue((ROOT/"site/lab04-research.js").exists())

 def test_dedicated_gemini_desk_and_news_source_links(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  app=(ROOT/"site/app.js").read_text(encoding="utf8")
  builder=(ROOT/"build_site.py").read_text(encoding="utf8")
  script=(ROOT/"site/lab04-desk.js").read_text(encoding="utf8")
  self.assertIn('data-view="desk"',html)
  self.assertIn('id="view-desk"',html)
  self.assertIn('id="desk-patchnotes"',html)
  self.assertIn('id="desk-news"',html)
  self.assertIn('id="desk-placements"',html)
  self.assertIn('lab04-desk.js?v=4.8',html)
  self.assertIn("'analysis','explore','desk'",app)
  self.assertIn('data["gemini_desk"]',builder)
  self.assertIn("textContent",script)
  self.assertIn("federalreserve.gov",script)
  self.assertNotIn("innerHTML",script)

 def test_persistent_strategy_foundry_is_visible_and_read_only(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  builder=(ROOT/"build_site.py").read_text(encoding="utf8")
  js=(ROOT/"site/lab04-research.js").read_text(encoding="utf8")
  workflow=(ROOT/".github/workflows/research.yml").read_text(encoding="utf8")
  self.assertIn('id="strategy-foundry-panel"',html)
  self.assertIn('id="strategy-foundry-ideas"',html)
  self.assertIn('lab04-research.js?v=4.6',html)
  self.assertIn('data["strategy_foundry"]',builder)
  self.assertIn('const foundry=DATA.strategy_foundry||{}',js)
  self.assertIn('textContent',js)
  self.assertNotIn('innerHTML',js)
  self.assertIn('python -m research.strategy_foundry',workflow)
  for tab in ("home","robots","analysis","explore","desk"):
   self.assertIn('data-view="'+tab+'"',html)

 def test_operational_roadmap_and_hourly_studies(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  builder=(ROOT/"build_site.py").read_text(encoding="utf8")
  script=(ROOT/"site/lab04-ops.js").read_text(encoding="utf8")
  self.assertIn('id="lab-operations-panel"',html)
  self.assertIn('id="lab-hourly-panel"',html)
  self.assertIn('id="operations-roadmap"',html)
  self.assertIn('lab04-ops.js?v=1',html)
  self.assertIn('data["intraday_study"]',builder)
  self.assertIn('data["operations"]',builder)
  self.assertIn("textContent",script)
  self.assertNotIn("innerHTML",script)

 def test_existing_strategy_sheet_and_bottom_tabs_are_stable(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  app=(ROOT/"site/app.js").read_text(encoding="utf8")
  directory=(ROOT/"site/lab04-directory.js").read_text(encoding="utf8")
  self.assertIn('class="bottom-nav"',html)
  self.assertIn('id="robot-sheet"',html)
  self.assertIn('id="close-sheet"',html)
  self.assertIn("function closeSheet()",app)
  self.assertIn("function detailSheet(r)",directory)
  self.assertIn("data-view=\"robots\"",html)

 def test_user_bottom_navigation_remains_unchanged_and_daily_brief_visible(self):
  template=(ROOT/"site/index.html").read_text(encoding="utf8")
  app=(ROOT/"site/app.js").read_text(encoding="utf8")
  source=(ROOT/"site/lab04-desk.js").read_text(encoding="utf8")
  builder=(ROOT/"build_site.py").read_text(encoding="utf8")
  workflow=(ROOT/".github/workflows/research.yml").read_text(encoding="utf8")
  self.assertIn('class="bottom-nav"',template)
  self.assertIn('data-view="robots"',template)
  self.assertIn('data-view="analysis"',template)
  self.assertIn('data-view="desk"',template)
  self.assertIn('data-view="explore"',template)
  self.assertNotIn('class="sheet-actions"',template)
  self.assertIn("historyApi.replaceState",app)
  self.assertNotIn("SeikoNavigation",app)
  self.assertIn('id="desk-daily-panel"',template)
  self.assertIn('id="desk-daily-date"',template)
  self.assertIn('id="desk-daily-content"',template)
  self.assertIn("daily_briefs",source)
  self.assertIn("textContent",source)
  self.assertNotIn("innerHTML",source)
  self.assertIn('reports/ai_daily_brief.json',builder)
  self.assertIn('python -m research.daily_brief',workflow)
  self.assertIn('test_daily_brief.py',workflow)

 def test_bottom_tabs_remain_visible(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  self.assertIn('class="bottom-nav"',html)

 def test_beginner_first_mode_is_complete_without_navigation_changes(self):
  html=(ROOT/"site/index.html").read_text(encoding="utf8")
  js=(ROOT/"site/lab04-simple.js").read_text(encoding="utf8")
  css=(ROOT/"site/lab04-simple.css").read_text(encoding="utf8")
  self.assertIn('lab04-simple.js?v=6',html)
  self.assertIn('lab04-simple.css?v=6',html)
  self.assertIn('ait-beginner-note',html)
  self.assertIn('Comprendre capital, position et rendement',html)
  self.assertIn('class="lab-advanced"',html)
  self.assertEqual(html.count("<details"),html.count("</details>"))
  for tab in ("home","robots","analysis","explore","desk"):
   self.assertIn('data-view="'+tab+'"',html)
  self.assertIn("ait-beginner-snapshot",js)
  self.assertIn("money", (ROOT/"site/lab04-clarity.js").read_text(encoding="utf8"))
  self.assertIn("ait-summary-grid",css)
  self.assertNotIn("innerHTML",js)

 def test_workflow_publishes_versions(self):
  workflow=(ROOT/".github/workflows/simulate.yml").read_text(encoding="utf8")
  self.assertIn("cp site/lab04-*.js docs/",workflow)
  self.assertIn("cp site/lab04-*.css docs/",workflow)

if __name__=="__main__":
 unittest.main()
