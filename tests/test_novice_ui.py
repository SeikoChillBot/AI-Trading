"""Quick structural checks for the simple AIT dashboard."""
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class UIChecks(unittest.TestCase):
    def test_unique_ids_and_five_bottom_tabs(self):
        page=(ROOT/"site/index.html").read_text(encoding="utf8")
        ids=re.findall(r'\bid="([^"]+)"',page)
        self.assertEqual(len(ids),len(set(ids)))
        nav=page.split('<nav class="bottom-nav"',1)[1].split('</nav>',1)[0]
        self.assertEqual(re.findall(r'data-view="([^"]+)"',nav),
                         ['home','robots','analysis','desk','explore'])
    def test_sections_and_optional_details(self):
        page=(ROOT/"site/index.html").read_text(encoding="utf8")
        self.assertEqual(page.count("<details"),page.count("</details>"))
        for section in ("ait-beginner-note","sheet-units","sheet-cash",
                        "sheet-chart","whale-radar-follow-list",
                        "base-usdc-list","desk-daily-content"):
            self.assertIn(section,page)
        self.assertIn('class="lab-advanced',page)

if __name__=="__main__":
    unittest.main()
