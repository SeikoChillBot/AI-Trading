"""Offline tests: no uncontrolled Gemini trades, no fabricated headlines."""
import unittest
from datetime import datetime,timezone,timedelta
from research import scenario_lab, ai_notebook, news_watch
from research.ai_decision_support import validate_model_ideas

NOW=datetime(2026,10,29,0,0,tzinfo=timezone.utc)

class DeskTests(unittest.TestCase):
    def test_structured_model_trials_are_bounded(self):
        payload={"summary":"Analyse prudente des données BTC",
                 "experiments":[],"bot_adjustments":[],
                 "scenario_proposals":[{"asset":"BTCUSD","trigger":"market_selloff",
                       "horizon_days":3,
                       "rationale":"Comparer un essai fictif de rebond avec la conservation de cash."}],
                 "desk_notes":[{"category":"risque","text":"Les données prospectives manquent encore."}]}
        result=validate_model_ideas(payload,{})
        self.assertEqual(result["scenario_proposals"][0]["horizon_days"],3)
        self.assertEqual(result["desk_notes"][0]["category"],"risque")
        payload["scenario_proposals"][0]["asset"]="DOGEUSD"
        with self.assertRaises(ValueError):validate_model_ideas(payload,{})

    def test_whale_samples_are_not_equated_to_buys(self):
        pulse={"generated_at":NOW.isoformat(),
               "assets":{"ETHUSD":{"change_7d_pct":-2}},
               "large_transfers":{"state":"observing",
                    "coverage":"NOT_EXHAUSTIVE_first_page_only_per_contract",
                    "new_in_sample":0}}
        idea={"asset":"ETHUSD","trigger":"sampled_large_transfer","horizon_days":1}
        ok,reason=scenario_lab.eligible(NOW,idea,pulse)
        self.assertFalse(ok)
        self.assertEqual(reason,"no_fresh_public_large_transfer_sample")

    def test_market_trial_has_no_instant_historical_return_and_stays_paper(self):
        seed=int(NOW.timestamp())-2*86400
        bars=[{"t":seed-i*86400,"close":100} for i in range(25)]
        bars=sorted(bars,key=lambda x:x["t"])
        pulse={"generated_at":NOW.isoformat(),"assets":{"BTCUSD":{"change_7d_pct":-2}}}
        ideas={"source":"gemini_generate_content",
            "scenario_proposals":[{"asset":"BTCUSD","trigger":"market_selloff",
                "horizon_days":1,"rationale":"Comparer l'entrée fictive à un témoin cash."}]}
        report,state=scenario_lab.evolve(NOW,ideas,pulse,{"BTCUSD":bars},{})
        self.assertEqual(len(report["trials"]),1)
        self.assertEqual(report["trials"][0]["equity_usd"],20)
        self.assertEqual(report["trials"][0]["status"],"waiting_next_closed_day")
        again,_=scenario_lab.evolve(NOW,ideas,pulse,{"BTCUSD":bars},state)
        self.assertEqual(len(again["trials"]),1)
        self.assertFalse(again["controls"]["real_orders"])
        # Only a future observed close can initialize the separate paper experiment.
        future=bars+[{"t":bars[-1]["t"]+86400,"close":99}]
        later=NOW+timedelta(days=1)
        p2,_=scenario_lab.evolve(later,{},pulse,{"BTCUSD":future},state)
        self.assertEqual(p2["trials"][0]["status"],"in_paper_position")

    def test_news_host_and_date_validation(self):
        xml=b'<rss><channel><item><title>Inflation update</title><link>https://www.federalreserve.gov/newsevents/x.htm</link><pubDate>Thu, 29 Oct 2026 00:00:00 GMT</pubDate></item></channel></rss>'
        ok=news_watch.parse_feed(xml,"Fed","www.federalreserve.gov","macro",NOW)
        self.assertEqual(len(ok),1)
        forged=xml.replace(b'www.federalreserve.gov',b'fake-news.example')
        self.assertEqual(news_watch.parse_feed(forged,"Fed","www.federalreserve.gov","macro",NOW),[])

    def test_patchnotes_cannot_invent_automated_changes(self):
        data={"ai":{"source":"gemini_generate_content","state":"model_reflection_completed",
                    "summary":"Etude en cours","desk_notes":[]},
              "status":{"model_last_called_at":NOW.isoformat(),"state":"model_reflection_completed","provider":"gemini"},
              "evolution":{"events_this_cycle":[],"counts":{"tracked":36}},
              "experiments":{"events":[],"trials":[]},
              "news":{"status":"available","articles":[]},"pulse":{}}
        log,state=ai_notebook.build(NOW,data,{})
        self.assertTrue(any(x["type"]=="ai_note" for x in log["entries"]))
        self.assertFalse(any(x["type"]=="patchnote" for x in log["entries"]))
        log2,_=ai_notebook.build(NOW,data,state)
        self.assertEqual(len(log2["entries"]),len(log["entries"]))

if __name__=="__main__":unittest.main()
