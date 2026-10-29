"""Offline safety tests for per-robot Gemini changes, prospective gates and controls."""
import unittest
from datetime import datetime, timezone, timedelta
from research import robot_tuning, robot_evolution as evolution, robot_shadow
from research.ai_decision_support import validate_model_ideas
from bot import decide

NOW = datetime(2026,10,28,23,50,tzinfo=timezone.utc)

class RobotEvolutionTests(unittest.TestCase):
    def test_all_36_have_distinct_names_and_hold_immutable(self):
        self.assertEqual(len(robot_tuning.ALL_ROBOTS),36)
        self.assertEqual(len(robot_tuning.CRYPTO_HOLD | robot_tuning.MULTI_HOLD),12)
        accepted=robot_tuning.validate_active({
            "schema":1, "profiles":{
                "btc_hold":{"entry_scale":.8,"source":"automatic_prospective_validation","approved_at":"now"},
                "btc_momentum":{"entry_scale":1.2,"source":"automatic_prospective_validation","approved_at":"now"},
                "sol_reversion":{"entry_scale":2,"source":"automatic_prospective_validation","approved_at":"now"}}})
        self.assertEqual(accepted,{"btc_momentum":1.2})

    def test_model_cannot_propose_code_arbitrary_names_or_unapproved_scales(self):
        evidence={"BTCUSD":{"asset":"BTCUSD","research_checks":{}}}
        response={"summary":"Modifications prudentes", "experiments":[],
                  "bot_adjustments":[{"strategy":"btc_momentum","profile":"conservative",
                                      "reason":"Tester si ce seuil freine les entrées coûteuses."}]}
        normalized=validate_model_ideas(response,evidence)
        self.assertEqual(normalized["bot_adjustments"][0]["entry_scale"],1.2)
        response["bot_adjustments"][0]["strategy"]="btc_hold"
        with self.assertRaises(ValueError):
            validate_model_ideas(response,evidence)
        response["bot_adjustments"][0]["strategy"]="__import__('os').system('echo unsafe')"
        with self.assertRaises(ValueError):
            validate_model_ideas(response,evidence)

    def test_build_all_36_and_does_not_change_early(self):
        research={"labs":{
            "crypto":{"strategies":[{"strategy":name,"asset":"BTCUSD",
                                     "net_return_pct":-1.4,"ready_for_review":False}
                                    for name in robot_tuning.TUNABLE_CRYPTO | robot_tuning.CRYPTO_HOLD]},
            "multi":{"strategies":[{"strategy":name,"asset":"SPY",
                                    "net_return_pct":0,"ready_for_review":False}
                                   for name in robot_tuning.TUNABLE_MULTI | robot_tuning.MULTI_HOLD]},
        }}
        ideas={"state":"model_reflection_completed","source":"gemini_generate_content",
               "bot_adjustments":[{"strategy":"btc_momentum","entry_scale":1.2,
                                    "reason":"Hypothèse de réduction des fausses entrées en tendance."}]}
        output,reg,active,events=evolution.build(NOW,research,ideas,{}, {}, {})
        self.assertEqual(output["counts"]["tracked"],36)
        self.assertEqual(output["counts"]["immutable_benchmarks"],12)
        self.assertEqual(output["counts"]["testing"],4)
        self.assertEqual(active["profiles"],{})
        pending=next(x for x in output["robots"] if x["strategy"]=="btc_momentum")
        self.assertEqual(pending["validation_progress"]["minimum_days"],14)
        self.assertEqual(pending["validation_progress"]["minimum_closed_trades"],20)
        hold=next(x for x in output["robots"] if x["strategy"]=="btc_hold")
        self.assertIsNone(hold["validation_progress"])
        self.assertEqual(events[0]["action"],"proposed_by_gemini")
        self.assertEqual(sum(x["action"]=="proposed_by_quant_engine" for x in events),3)
        again,reg2,active2,events2=evolution.build(NOW,research,ideas,{},reg,active)
        self.assertEqual(len(events2),3)
        self.assertTrue(all(x["action"]=="proposed_by_quant_engine" for x in events2))
        self.assertEqual(reg2["candidates"]["btc_momentum"]["created_at"],NOW.isoformat())

    def test_all_individual_bots_receive_bounded_prospective_studies(self):
        research={"labs":{
          "crypto":{"strategies":[{"strategy":name,"drawdown_pct":0} for name in
                  robot_tuning.TUNABLE_CRYPTO | robot_tuning.CRYPTO_HOLD]},
          "multi":{"strategies":[{"strategy":name,"drawdown_pct":0} for name in
                 robot_tuning.TUNABLE_MULTI | robot_tuning.MULTI_HOLD]}}}
        state,active={},{}
        for _ in range(7):
            output,state,active,events=evolution.build(NOW,research,{}, {},state,active)
        self.assertEqual(len(state["candidates"]),24)
        self.assertEqual(output["counts"]["testing"],24)
        self.assertEqual(active["profiles"],{})
        self.assertTrue(all(x["source"]=="automatic_statistical_shadow" for x in state["candidates"].values()))

    def test_minimum_days_trades_fee_stress_and_drawdown(self):
        candidate={"created_at":(NOW-timedelta(days=15)).isoformat(),"lab":"crypto",
                   "entry_scale":1.2}
        evidence={"source":"independent_forward_shadow_v1",
                  "created_at":candidate["created_at"],"observed_at":NOW.isoformat(),
                  "entry_scale":1.2,"ready_for_real_orders":False,"observations":201,
                  "control":{"net_return_pct":1,"max_drawdown_pct":10},
                  "candidate":{"net_return_pct":5,"closed_trades":23,
                               "stress_net_return_pct":1,"max_drawdown_pct":8}}
        yes,blocks=evolution.sufficient_prospective(evidence,candidate,NOW)
        self.assertTrue(yes)
        evidence["candidate"]["stress_net_return_pct"]=-1
        no,blocks=evolution.sufficient_prospective(evidence,candidate,NOW)
        self.assertFalse(no)
        self.assertIn("double_fees_not_loss",blocks)

    def test_future_validation_requires_contiguous_evidence(self):
        candidate={"created_at":(NOW-timedelta(days=17)).isoformat(),
                   "lab":"crypto","entry_scale":1.2}
        evidence={"source":"independent_forward_shadow_v1",
                  "created_at":candidate["created_at"],
                  "observed_at":NOW.isoformat(),"entry_scale":1.2,
                  "ready_for_real_orders":False,"observations":130,
                  "missed_observations":5,
                  "control":{"net_return_pct":1,"max_drawdown_pct":10},
                  "candidate":{"net_return_pct":5,"closed_trades":25,
                    "stress_net_return_pct":2,"max_drawdown_pct":8}}
        ok,blocked=evolution.sufficient_prospective(evidence,candidate,NOW)
        self.assertFalse(ok)
        self.assertIn("bounded_missing_market_observations",blocked)
        evidence["missed_observations"]=0
        evidence["observed_at"]=(NOW+timedelta(hours=1)).isoformat()
        ok,blocked=evolution.sufficient_prospective(evidence,candidate,NOW)
        self.assertFalse(ok)

    def test_shadow_first_registration_never_replays_old_profit(self):
        candidate={"created_at":NOW.isoformat(),"entry_scale":1.2}
        record=robot_shadow.start(candidate,100)
        self.assertEqual(record["observations"],0)
        self.assertEqual(record["candidate"]["cash"],20)
        record=robot_shadow.process_one(record,200,100,lambda label,scale,held:"BUY",.009)
        self.assertEqual(record["observations"],1)
        self.assertEqual(record["candidate"]["net_return_pct"],0)
        record=robot_shadow.process_one(record,300,101,lambda label,scale,held:"WAIT",.009)
        self.assertLess(record["candidate"]["net_return_pct"],1)
        self.assertFalse(robot_shadow.summarize(NOW,candidate,record)["ready_for_real_orders"])

    def test_default_signal_is_backwards_compatible(self):
        closes=[100+(i%4) for i in range(65)]
        self.assertEqual(decide("momentum",closes,False),
                         decide("momentum",closes,False,threshold_scale=1.0))
        with self.assertRaises(ValueError):
            decide("momentum",closes,False,threshold_scale=4.0)

if __name__=="__main__":unittest.main()
