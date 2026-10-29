"""AIT director: model provenance, question-first autonomy and future-only feedback."""
import unittest
from datetime import datetime, timezone, timedelta

from research import research_director as director
from research import strategy_foundry as foundry
from research import ai_decision_support as decisions

NOW = datetime(2026, 10, 29, 22, tzinfo=timezone.utc)
START = int(NOW.timestamp()) // 86400 * 86400 - 720 * 86400


def candles():
    return {a:[
        {"t":START+i*86400, "open":100+i/20, "close":100+(i+1)/20}
        for i in range(720)] for a in foundry.ASSETS}


def science():
    return {
        "schema": 1, "state":"research_memory_recorded",
        "real_orders":False, "no_causal_attribution":True,
        "no_promotions":True, "research_agenda":[
            {"category":"cost_sensitivity","failed_historical_checks":15},
            {"category":"trade_density","failed_historical_checks":13},
            {"category":"hold_comparison","failed_historical_checks":7}],
    }


def model_spec():
    return {
        "asset":"BTCUSD", "logic":"ema_trend", "lookback_days":40,
        "threshold_pct":.5, "max_hold_days":7,
        "confirmations":["ema_uptrend","rsi_strength"],
        "rationale":"Tester une entrée plus prudente après coûts et témoin Hold.",
    }


def proposal():
    return {"source":"gemini_generate_content", "state":"model_reflection_completed",
            "provider":"gemini", "model_last_called_at":NOW.isoformat(),
            "used_cache":False, "real_orders_enabled":False,
            "live_strategy_changes_enabled":False,
            "research_tasks":[{
                "asset":"BTCUSD", "goal":"cost_resilience",
                "hypothesis":"Deux confirmations pourraient améliorer le net après frais.",
                "rejection_rule":"Rejeter si le résultat prospectif est inférieur au témoin Hold.",
                "strategy":model_spec(),
            }]}


class ResearchDirectorTests(unittest.TestCase):
    def go(self, proposals=None, previous=None, forward=None,
           knowledge=None, science_state=None, now=NOW):
        return director.build(now, candles(), science(), science_state or {
            "seen_spec_ids":[],"real_orders":False,
            "robots_modified":False}, proposals or {},
            knowledge or {"ideas":[]}, forward or {}, previous or {})

    def test_gemini_proposal_is_explicit_and_frozen_before_paper(self):
        report,state=self.go(proposals=proposal())
        self.assertEqual(report["model_directed_this_cycle"],1)
        self.assertEqual(report["tracked"],3)
        btc=next(x for x in state["experiments"] if x["asset"]=="BTCUSD")
        self.assertEqual(btc["source"],"gemini_research_director")
        self.assertEqual(btc["goal"],"cost_resilience")
        self.assertEqual(btc["id"],foundry.identifier(foundry.normalise(model_spec())))
        self.assertFalse(report["real_orders"])
        self.assertFalse(report["robot_changes"])
        self.assertTrue(btc["historical_data_not_independent_validation"])
        second,new_state=self.go(proposals=proposal(),previous=state)
        self.assertEqual(second["model_directed_this_cycle"],0)
        self.assertEqual(second["local_fallback_new_experiments"],0)
        self.assertEqual(len(new_state["experiments"]),3)

    def test_fallback_is_labelled_and_research_aim_rotates_by_asset(self):
        report,state=self.go()
        self.assertEqual(report["model_directed_this_cycle"],0)
        self.assertEqual(report["local_fallback_new_experiments"],3)
        self.assertEqual([x["goal"] for x in state["experiments"]],
                         ["cost_resilience","trade_frequency","beat_hold"])
        self.assertTrue(all(x["source"]=="bounded_local_research_director"
                            for x in state["experiments"]))

    def test_forged_or_stale_models_cannot_dispatch(self):
        for mutation in ({"model_last_called_at":(NOW-timedelta(days=2)).isoformat()},
                         {"real_orders_enabled":True},
                         {"source":"deterministic_fallback"},
                         {"research_tasks":[{**proposal()["research_tasks"][0],
                            "strategy":{**model_spec(),"logic":"exec"}}]}):
            forged={**proposal(),**mutation}
            report,state=self.go(proposals=forged)
            self.assertEqual(report["model_directed_this_cycle"],0)
            self.assertEqual(len(state["experiments"]),3)
        with self.assertRaises(ValueError):
            director._checked_plan({**proposal()["research_tasks"][0],
              "rejection_rule":"Non."},"BTCUSD")

    def test_only_real_future_observation_can_close_a_loop(self):
        _,state=self.go()
        btc=next(x for x in state["experiments"] if x["asset"]=="BTCUSD")
        rec={"id":btc["id"], "spec":btc["spec"],
             "status":"observing_paper_only","observed_days":89,
             "closed_trades":100, "net_pct":-100,
             "excess_vs_hold_points":-1,"max_drawdown_pct":50}
        self.assertEqual(director.prospective_status(btc,{"tracks":{btc["id"]:rec}})[0],
                         "awaiting_prospective_data")
        rec["observed_days"]=90
        rec["closed_trades"]=10
        self.assertEqual(director.prospective_status(btc,{"tracks":{btc["id"]:rec}})[0],
                         "prospectively_contradicted")
        rec["net_pct"]=10
        rec["excess_vs_hold_points"]=3
        rec["max_drawdown_pct"]=5
        self.assertEqual(director.prospective_status(btc,{"tracks":{btc["id"]:rec}})[0],
                         "tentatively_supported_paper_only")
        rec["spec"]={**btc["spec"],"threshold_pct":2}
        self.assertEqual(director.prospective_status(btc,{"tracks":{btc["id"]:rec}})[0],
                         "invalid_forward_provenance")

    def test_unverified_scientific_memory_cannot_launch_new_experiments(self):
        report, state = self.go(science_state={"seen_spec_ids":[],
                                              "real_orders":True,
                                              "robots_modified":False})
        self.assertEqual(report["tracked"],0)
        self.assertEqual(len(report["issues"]),3)
        self.assertTrue(all(v=="unverified_scientific_evidence"
                            for v in report["issues"].values()))
        self.assertEqual(state["experiments"],[])
        self.assertFalse(report["real_orders"])

    def test_validated_model_plan_is_kept_separate_from_bot_adjustments(self):
        validated=decisions.validate_model_ideas({
            "summary":"Analyse avec une proposition structurée et falsifiable.",
            "experiments":[], "bot_adjustments":[], "scenario_proposals":[],
            "desk_notes":[], "strategy_designs":[],
            "research_tasks":proposal()["research_tasks"],
        }, {"BTCUSD":{}})
        self.assertEqual(len(validated["research_tasks"]),1)
        self.assertEqual(validated["bot_adjustments"],[])
        invalid=proposal()["research_tasks"][0].copy()
        invalid["goal"]="make_money_guaranteed"
        with self.assertRaises(ValueError):
            decisions.validate_model_ideas({
                "summary":"Analyse prudente de stratégie et de recherche.",
                "experiments":[], "bot_adjustments":[], "scenario_proposals":[],
                "desk_notes":[], "strategy_designs":[],
                "research_tasks":[invalid],
            }, {"BTCUSD":{}})


if __name__ == "__main__":
    unittest.main()
