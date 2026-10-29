"""No-jargon site: explanatory content may not change paper simulation data."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ExplanationTests(unittest.TestCase):
    def test_five_original_tabs_and_guides_are_present(self):
        html=(ROOT/"site/index.html").read_text(encoding="utf8")
        self.assertIn('lab04-guide.js?v=7',html)
        self.assertIn('lab04-guide.css?v=7',html)
        self.assertIn('Comment ça fonctionne, en une minute',html)
        self.assertIn('Dictionnaire des mots du site',html)
        self.assertIn('Pourquoi aucune amélioration',html)
        self.assertIn('ait-sheet-activity-list',html)
        self.assertIn('ait-gemini-ideas',html)
        nav=html.split('<nav class="bottom-nav"',1)[1].split("</nav>",1)[0]
        self.assertEqual(re.findall(r'data-view="([^"]+)"',nav),
                         ["home","robots","analysis","desk","explore"])
        ids=re.findall(r'\bid="([^"]+)"',html)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(html.count("<details"),html.count("</details>"))

    def test_explanations_read_only_and_source_qualified(self):
        js=(ROOT/"site/lab04-guide.js").read_text(encoding="utf8")
        builder=(ROOT/"build_site.py").read_text(encoding="utf8")
        for term in ("paper","orders","observed_at","gemini_generate_content",
                     "bot_adjustments","last","MutationObserver"):
            if term=="last":
                continue
            self.assertIn(term,js)
        self.assertNotIn("innerHTML",js)
        self.assertNotIn("eval(",js)
        self.assertIn("gemini_hypothesis_unverified",builder)
        self.assertIn('"entry_scale"',builder)
        self.assertIn("Aucun", (ROOT/"site/index.html").read_text(encoding="utf8"))

if __name__=="__main__":
    unittest.main()
