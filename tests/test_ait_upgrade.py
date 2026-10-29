"""Regression tests for AIT recovery: no secret, cash, or live trade needed."""
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from research import ai_reflection as ai, large_transfers as transfers, whale_follow as follow

NOW=datetime(2026,10,29,3,15,tzinfo=timezone.utc)
ADDR1="0x"+"1"*40
ADDR2="0x"+"2"*40


def sample_transfer(tx="0x"+"a"*64):
    return {
        "token":{"address_hash":transfers.CONTRACTS["USDC"]},
        "total":{"decimals":"6","value":"2500000000000"},
        "timestamp":"2026-10-29T03:10:00Z","transaction_hash":tx,
        "from":{"hash":ADDR1},"to":{"hash":ADDR2},"log_index":3
    }


class Response:
    def __init__(self,rows):self.rows=rows
    def raise_for_status(self):pass
    def json(self):return {"items":self.rows}


class RadarTests(unittest.TestCase):
    def test_sampled_wallet_flows_dont_infer_trades(self):
        def getter(url,**kwargs):
            token="USDC" if transfers.CONTRACTS["USDC"] in url else "USDT"
            if token=="USDC":
                return Response([sample_transfer()])
            return Response([])
        report,state=transfers.build(NOW,{},getter)
        self.assertEqual(report["large_transfers_observed"],1)
        self.assertEqual(report["large_transfers_new"],[])
        self.assertEqual(report["sampled_wallets_count"],2)
        self.assertEqual(report["sampled_wallet_flows"][0]["trade_inference"],"unknown")
        self.assertFalse(report["sampled_wallet_flows"][0]["identity_verified"])
        self.assertFalse(report["buy_sell_inference"])
        self.assertEqual(sum(x["sample_net_nominal_usd"] for x in
                             report["sampled_wallet_flows"]),0)

    def test_bounded_address_follow_baseline_then_new(self):
        source={"state":"observing","generated_at":NOW.isoformat(),
                "sampled_wallet_flows":[{"address":ADDR1,"identity_verified":False}]}
        rows=[sample_transfer()]
        getter=lambda url,**kw:Response(rows)
        report,state=follow.observe(NOW,source,{},getter)
        self.assertEqual(report["state"],"observing")
        self.assertEqual(len(report["tracked_addresses"]),1)
        self.assertEqual(report["new_transfers"],[])
        self.assertFalse(report["can_infer_owner"])
        self.assertFalse(report["can_infer_trade"])
        rows[:]=[sample_transfer("0x"+"b"*64)]
        again,_=follow.observe(NOW,source,state,getter)
        self.assertEqual(len(again["new_transfers"]),1)
        self.assertEqual(again["new_transfers"][0]["trade_inference"],"unknown")

    def test_stale_sample_prevents_address_follow(self):
        source={"state":"observing","generated_at":(NOW-timedelta(hours=5)).isoformat(),
                "sampled_wallet_flows":[{"address":ADDR1,"identity_verified":False}]}
        report,state=follow.observe(NOW,source,{},lambda *x,**kw:None)
        self.assertEqual(report["state"],"no_recent_addresses")
        self.assertEqual(report["new_transfers"],[])


class GeminiRecoveryTests(unittest.TestCase):
    def test_failed_request_cached_then_retried_once(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            # Test only control flow; actual credentials/HTTP never accessed.
            historical={"assets":[{"asset":"BTCUSD"}]}
            times=[datetime(2026,10,29,0,10,tzinfo=timezone.utc)]
            class Clock:
                @staticmethod
                def now(tz):return times[0]
                fromisoformat=staticmethod(datetime.fromisoformat)
            success={"summary":"Réponse réelle validée","experiments":[],
                     "bot_adjustments":[],"scenario_proposals":[],"desk_notes":[]}
            with (patch.object(ai,"DATA",folder/"ideas.json"),
                  patch.object(ai,"OUTPUT",folder/"ideas.md"),
                  patch.object(ai,"STATUS",folder/"status.json"),
                  patch.object(ai,"REPORT",folder/"research.json"),
                  patch.object(ai,"WALK",folder/"history.json"),
                  patch.object(ai,"datetime",Clock),
                  patch.object(ai,"summarize_challengers",return_value=historical),
                  patch.object(ai,"baseline_ideas",return_value=[]),
                  patch.object(ai,"readable",return_value="# Test"),
                  patch.object(ai,"run_gemini",side_effect=[ValueError("Invalid model JSON"),success]) as called,
                  patch.dict(os.environ,{"SEIKO_AI_ENABLED":"1",
                                         "SEIKO_AI_PROVIDER":"gemini",
                                         "GEMINI_API_KEY":"fake-for-test"},clear=True)):
                ai.main()
                ai.main()
                failed=json.loads((folder/"status.json").read_text())
                self.assertEqual(failed["state"],"model_reflection_failed")
                self.assertEqual(failed["error_type"],"ValueError")
                self.assertEqual(failed["attempts_in_slot"],1)
                times[0]=datetime(2026,10,29,2,10,tzinfo=timezone.utc)
                ai.main()
                repaired=json.loads((folder/"status.json").read_text())
                self.assertEqual(repaired["state"],"model_reflection_completed")
                self.assertEqual(repaired["attempts_in_slot"],2)
                self.assertIsNone(repaired["error_type"])
                self.assertEqual(called.call_count,2)

    def test_model_quota_not_retried_in_same_slot(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            at=datetime(2026,10,29,0,5,tzinfo=timezone.utc)
            status={"review_slot":"2026-10-29T00:00Z","provider":"gemini",
                    "state":"model_reflection_failed","last_http_status":429,
                    "last_attempt_at":at.isoformat(),"attempts_in_slot":1}
            (folder/"status.json").write_text(json.dumps(status),encoding="utf8")
            class Clock:
                @staticmethod
                def now(tz):return at+timedelta(hours=3)
                fromisoformat=staticmethod(datetime.fromisoformat)
            with (patch.object(ai,"DATA",folder/"ideas.json"),
                  patch.object(ai,"OUTPUT",folder/"ideas.md"),
                  patch.object(ai,"STATUS",folder/"status.json"),
                  patch.object(ai,"REPORT",folder/"research.json"),
                  patch.object(ai,"WALK",folder/"history.json"),
                  patch.object(ai,"datetime",Clock),
                  patch.object(ai,"summarize_challengers",return_value={"assets":[{"asset":"BTCUSD"}]}),
                  patch.object(ai,"baseline_ideas",return_value=[]),
                  patch.object(ai,"readable",return_value="# Test"),
                  patch.object(ai,"run_gemini",side_effect=AssertionError("Never retry 429")),
                  patch.dict(os.environ,{"SEIKO_AI_ENABLED":"1","SEIKO_AI_PROVIDER":"gemini",
                                         "GEMINI_API_KEY":"fake-for-test"},clear=True)):
                ai.main()
            result=json.loads((folder/"status.json").read_text())
            self.assertEqual(result["state"],"model_reflection_failed")
            self.assertEqual(result["attempts_in_slot"],1)
            self.assertTrue(result["used_cache"])


    def test_gemini_schema_400_recovers_with_json_only_still_validated(self):
        sample={"summary":"Vérifier les risques","experiments":[],
                "bot_adjustments":[],"scenario_proposals":[],"desk_notes":[]}
        output={"candidates":[{"finishReason":"STOP",
                "content":{"parts":[{"text":json.dumps(sample)}]}}]}
        class APIResponse:
            def __init__(self,status_code):self.status_code=status_code
            def raise_for_status(self):
                if self.status_code>=400:
                    raise ai.requests.HTTPError("Bad request",response=self)
            def json(self):return output
        calls=[]
        def post(url,**kwargs):
            calls.append(kwargs["json"])
            return APIResponse(400 if len(calls)<3 else 200)
        with patch.object(ai.requests,"post",post):
            data=ai.run_gemini("fake-test-only",{},
                               {"assets":[{"asset":"BTCUSD"}]})
        self.assertEqual(data["summary"],sample["summary"])
        self.assertEqual(len(calls),3)
        self.assertNotIn("responseSchema",calls[2]["generationConfig"])
        self.assertEqual(calls[2]["generationConfig"]["responseMimeType"],"application/json")



class DashboardTests(unittest.TestCase):
    def test_original_navigation_and_new_panels(self):
        root=Path(__file__).resolve().parents[1]
        html=(root/"site/index.html").read_text(encoding="utf8")
        source=(root/"site/lab04-clarity.js").read_text(encoding="utf8")
        self.assertIn('class="bottom-nav"',html)
        for name in ("home","robots","analysis","desk","explore"):
            self.assertIn('data-view="'+name+'"',html)
        for name in ("sheet-initial","sheet-cash","sheet-units","sheet-position",
                     "whale-radar-follow-list","lab-freshness-badge",
                     "lab-gemini-diagnostic"):
            self.assertIn('id="'+name+'"',html)
        self.assertIn("MutationObserver",source)
        self.assertIn("sampled_wallet_flows",source)
        self.assertNotIn('class="sheet-actions"',html)


if __name__=="__main__":
    unittest.main()
