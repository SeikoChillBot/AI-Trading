"""Offline tests: research evidence, LLM isolation, and safe defaults."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from research import ai_decision_support as support
from research import ai_reflection as ai

NOW = datetime(2026, 10, 28, 23, 0, tzinfo=timezone.utc)


def sample_report():
    folds = []
    for i in range(8):
        folds.append({
            "oos_return_pct": 5 if i % 2 else -4,
            "hold_return_pct": 3 if i % 2 else -2,
            "excess_vs_hold_points": 2 if i % 2 else -2,
            "cost_x2_return_pct": 2 if i % 2 else -6,
            "observed_drawdown_pct": 10 + i,
            "completed_trades": 1,
        })
    return {
        "model": support.MODEL,
        "generated_at": NOW.isoformat(),
        "instruments": {
            "ETHUSD": {"folds": folds, "fold_count": len(folds),
                       "candidate_parameters": {"window": 20, "buffer": .01}}
        },
    }


class EvidenceTests(unittest.TestCase):
    def test_research_does_not_claim_profitability(self):
        report = support.summarize_challengers(sample_report(), NOW)
        eth = report["assets"][0]
        self.assertEqual(eth["asset"], "ETHUSD")
        self.assertEqual(eth["closed_trades"], 8)
        self.assertFalse(eth["research_checks"]["twenty_or_more_closed_trades"])
        self.assertFalse(eth["automatic_promotion"])
        self.assertFalse(report["eligible_for_automatic_promotion"])

    def test_stale_or_modified_or_incomplete_data_is_rejected(self):
        self.assertEqual(
            support.summarize_challengers(sample_report(), NOW + timedelta(days=4))["assets"], []
        )
        report = sample_report()
        report["instruments"]["ETHUSD"]["folds"][0]["oos_return_pct"] = float("inf")
        self.assertEqual(support.summarize_challengers(report, NOW)["assets"], [])

    def test_safe_prompt_does_not_contain_wallet_information(self):
        context = support.safe_context(
            {"labs": {"crypto": {"count": 18, "secret": "never-expose-this"},
                      "multi": {}}, "hypotheses": []},
            support.summarize_challengers(sample_report(), NOW))
        self.assertNotIn("never-expose-this", json.dumps(context))
        self.assertEqual(context["budget_per_strategy_usd"], 20)
        self.assertFalse(context["allow_live_strategy_changes"])

    def test_unknown_assets_and_nonfalsifiable_ideas_blocked(self):
        data = {"summary": "Hypothèse", "experiments": [
            {"asset": "DOGEUSD", "title": "Tester un filtre",
             "hypothesis": "Possibilité sans preuve", "experiment": "Un test hors échantillon",
             "rejection_rule": "Abandon si échec net"}]}
        evidence = support.summarize_challengers(sample_report(), NOW)
        with self.assertRaises(ValueError):
            support.validate_model_ideas(data, {v["asset"]: v for v in evidence["assets"]})

    def test_model_request_is_schema_bound_and_has_no_tools(self):
        response = {"output": [{"type": "message", "content": [{
            "type": "output_text",
            "text": json.dumps({"summary": "Frais possiblement excessifs",
                                "experiments": []})
        }]}]}
        class FakeResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return response
        captured = []
        def fake_post(url, **kwargs):
            captured.append(kwargs["json"])
            return FakeResponse()
        historical = support.summarize_challengers(sample_report(), NOW)
        with patch.object(ai.requests, "post", fake_post):
            result = ai.run("test_key", "test_model", {}, historical)
        self.assertEqual(result["experiments"], [])
        self.assertFalse(captured[0]["store"])
        self.assertNotIn("tools", captured[0])
        self.assertEqual(captured[0]["text"]["format"]["type"], "json_schema")

    def test_gemini_free_model_and_structured_output(self):
        reply = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{
            "text": json.dumps({"summary": "Preuves historiques insuffisantes", "experiments": []})
        }]}}]}
        class FakeResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return reply
        captured = []
        def fake_post(url, **kwargs):
            captured.append((url, kwargs))
            return FakeResponse()
        historical = support.summarize_challengers(sample_report(), NOW)
        with patch.object(ai.requests, "post", fake_post):
            result = ai.run_gemini("mock_only", {}, historical)
        self.assertEqual(result["experiments"], [])
        self.assertIn("gemini-3.5-flash-lite", captured[0][0])
        self.assertEqual(captured[0][1]["json"]["generationConfig"]["responseMimeType"], "application/json")
        self.assertNotIn("tools", captured[0][1]["json"])
        self.assertEqual(captured[0][1]["headers"]["x-goog-api-key"], "mock_only")

    def test_gemini_refuses_partial_or_unverified_answer(self):
        historical = support.summarize_challengers(sample_report(), NOW)
        class FakeResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return {"candidates": [{"finishReason": "MAX_TOKENS",
                                        "content": {"parts": [{"text": "{}"}]}}]}
        with patch.object(ai.requests, "post", return_value=FakeResponse()):
            with self.assertRaises(ValueError):
                ai.run_gemini("test", {}, historical)

    def test_gemini_selection_does_not_invoke_openai(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "research.json").write_text('{"labs":{}}', encoding="utf-8")
            example = sample_report()
            example["generated_at"] = datetime.now(timezone.utc).isoformat()
            (folder / "walk.json").write_text(json.dumps(example), encoding="utf-8")
            with (patch.object(ai, "REPORT", folder / "research.json"),
                  patch.object(ai, "WALK", folder / "walk.json"),
                  patch.object(ai, "DATA", folder / "ideas.json"),
                  patch.object(ai, "OUTPUT", folder / "ideas.md"),
                  patch.object(ai, "STATUS", folder / "status.json"),
                  patch.dict("os.environ", {"SEIKO_AI_ENABLED": "1",
                        "SEIKO_AI_PROVIDER": "gemini", "GEMINI_API_KEY": "test",
                        "OPENAI_API_KEY": "ignored-paid-key"}),
                  patch.object(ai, "run_gemini", return_value={
                      "summary": "Tests requis", "experiments": []}) as gemini,
                  patch.object(ai, "run", side_effect=AssertionError("OpenAI is not allowed"))):
                ai.main()
                ai.main()
            status = json.loads((folder / "status.json").read_text())
            self.assertEqual(status["state"], "model_reflection_completed")
            self.assertEqual(status["provider"], "gemini")
            self.assertEqual(gemini.call_count, 1)
            research = json.loads((folder / "ideas.json").read_text())
            self.assertEqual(research["source"], "gemini_generate_content")
            self.assertFalse(research["real_orders_enabled"])

    def test_gemini_http_400_falls_back_only_to_smaller_same_provider_schema(self):
        completed = {"candidates":[{"finishReason":"STOP","content":{"parts":[{
            "text":json.dumps({"summary":"Vérifier les frais","experiments":[],"bot_adjustments":[]})
        }]}}]}
        class Reply:
            def __init__(self,code):
                self.status_code=code
            def raise_for_status(self):
                if self.status_code >= 400:
                    response=self
                    raise ai.requests.HTTPError("Bad request",response=response)
            def json(self):return completed
        seen=[]
        def post(url,**kwargs):
            seen.append(kwargs["json"])
            return Reply(400 if len(seen)==1 else 200)
        historical=support.summarize_challengers(sample_report(),NOW)
        with patch.object(ai.requests,"post",post):
            out=ai.run_gemini("dummy",{},historical)
        self.assertEqual(out["experiments"],[])
        self.assertEqual(len(seen),2)
        self.assertEqual(set(seen[1]["generationConfig"]["responseSchema"]["properties"]),
                         {"summary","experiments","bot_adjustments"})

    def test_gemini_quota_has_no_retry_or_paid_fallback(self):
        class Reply:
            status_code=429
            def raise_for_status(self):
                raise ai.requests.HTTPError("Quota",response=self)
        calls=[]
        def post(url,**kwargs):
            calls.append(url)
            return Reply()
        historical=support.summarize_challengers(sample_report(),NOW)
        with patch.object(ai.requests,"post",post):
            with self.assertRaises(ai.requests.HTTPError):
                ai.run_gemini("dummy",{},historical)
        self.assertEqual(len(calls),1)

    def test_no_key_means_no_paid_request(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "research.json").write_text('{"labs":{}}', encoding="utf-8")
            (folder / "walk.json").write_text(json.dumps(sample_report()), encoding="utf-8")
            with (patch.object(ai, "REPORT", folder / "research.json"),
                  patch.object(ai, "WALK", folder / "walk.json"),
                  patch.object(ai, "DATA", folder / "ideas.json"),
                  patch.object(ai, "OUTPUT", folder / "ideas.md"),
                  patch.object(ai, "STATUS", folder / "status.json"),
                  patch.dict("os.environ", {"SEIKO_AI_ENABLED": "0", "OPENAI_API_KEY": ""}),
                  patch.object(ai.requests, "post", side_effect=AssertionError("No paid call"))):
                ai.main()
            results = json.loads((folder / "ideas.json").read_text())
            self.assertEqual(results["source"], "deterministic_fallback")
            self.assertFalse(results["real_orders_enabled"])
            self.assertFalse(results["live_strategy_changes_enabled"])


if __name__ == "__main__":
    unittest.main()
