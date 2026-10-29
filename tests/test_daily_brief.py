"""Daily journal must not claim Gemini authored a statistical fallback."""
import unittest
from datetime import datetime, timezone, timedelta
from research import daily_brief as journal

NOW = datetime(2026, 10, 29, 0, 30, tzinfo=timezone.utc)

class DailyBriefTests(unittest.TestCase):
    def sample(self):
        return {
            "model":{"generated_at":NOW.isoformat(),"state":"model_reflection_failed"},
            "proposals":{"source":"deterministic_fallback","state":"model_reflection_failed"},
            "journal":{"entries":[
                {"at":NOW.isoformat(),"type":"paper_test","title":"SOLUSD — nouveau test fictif"},
                {"at":NOW.isoformat(),"type":"news","title":"Fed — actualité"}]},
            "evolution":{"generated_at":NOW.isoformat(),"counts":{
                "tracked":36,"testing":16,"activated":0}},
            "experiments":{"trials":[
                {"id":"a","created_at":NOW.isoformat(),"actor":"quantitative_auto_fallback"},
                {"id":"b","created_at":NOW.isoformat(),"actor":"quantitative_auto_fallback"}]},
            "intraday":{"generated_at":NOW.isoformat(),"assets":{
                "BTCUSD":{"historical_study":{"avg_excess_vs_hold":-1}},
                "ETHUSD":{"historical_study":{"avg_excess_vs_hold":-2}},
                "SOLUSD":{"historical_study":{"avg_excess_vs_hold":-3}}}},
            "whales":{"generated_at":NOW.isoformat(),"sampled_records":{"USDC":150,"USDT":150}},
            "news":{},
        }

    def test_fallback_is_not_misattributed_to_gemini(self):
        events=[
            {"at":NOW.isoformat(),"action":"proposed_by_quant_engine","robot":"btc_momentum"},
            {"at":NOW.isoformat(),"action":"proposed_by_quant_engine","robot":"eth_momentum"},
        ]
        out, _ = journal.build(NOW,self.sample(),events,{})
        day=out["days"][0]
        self.assertEqual(day["date"],"2026-10-29")
        self.assertIsNone(day["gemini_authored_summary"])
        self.assertEqual(day["gemini_status"],"model_reflection_failed")
        self.assertIn("échec API", " ".join(day["conclusions"]))
        self.assertEqual(day["counts"]["quant_robot_proposals"],2)
        self.assertEqual(day["counts"]["gemini_robot_proposals"],0)
        self.assertEqual(day["counts"]["new_paper_trials"],2)
        self.assertEqual(day["counts"]["news_articles_in_journal"],1)
        self.assertFalse(out["real_orders"])

    def test_real_model_summary_requires_recorded_same_day_note(self):
        data=self.sample()
        data["model"]["state"]="model_reflection_completed"
        data["proposals"]["source"]="gemini_generate_content"
        data["journal"]["entries"].append({
            "type":"ai_note","at":NOW.isoformat(),
            "title":"Analyse Gemini — synthèse",
            "details":"Pas de stratégie robuste après frais."
        })
        out,_=journal.build(NOW,data,[],{})
        day=out["days"][0]
        self.assertEqual(day["gemini_authored_summary"],"Pas de stratégie robuste après frais.")
        self.assertIn("réellement publiée par Gemini", " ".join(day["conclusions"]))
        # The previous day's Gemini note is not evidence for today.
        data["journal"]["entries"][-1]["at"]=(NOW-timedelta(days=1)).isoformat()
        out,_=journal.build(NOW,data,[],{})
        self.assertIsNone(out["days"][0]["gemini_authored_summary"])

    def test_multiple_runs_update_same_day_and_archive_previous(self):
        initial,state=journal.build(NOW,self.sample(),[],{})
        again,state2=journal.build(NOW+timedelta(minutes=20),self.sample(),[],state)
        self.assertEqual(len(again["days"]),1)
        self.assertEqual(again["days"][0]["period"],"in_progress")
        tomorrow=NOW+timedelta(days=1)
        report,_=journal.build(tomorrow,{},[],state2)
        self.assertEqual([v["date"] for v in report["days"]],
                         ["2026-10-30","2026-10-29"])
        self.assertEqual(report["days"][1]["period"],"closed_snapshot")

    def test_midnight_in_paris_uses_local_date_not_utc(self):
        at=datetime(2026,10,28,23,40,tzinfo=timezone.utc)
        self.assertEqual(journal.date_of(at.isoformat()),"2026-10-29")
        item=journal.events_from_lines('bad\n{"at":"2026-10-28T23:40:00+00:00","action":"proposed_by_quant_engine","robot":"sol_momentum"}')
        self.assertEqual(len(item),1)

if __name__=="__main__":
    unittest.main()
