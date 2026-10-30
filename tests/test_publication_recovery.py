"""Offline regression tests for AIT stale-checkout and safe retry protection."""
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import requests
from research import publication_recovery as recovery

NOW = datetime(2026, 10, 30, 7, 0, tzinfo=timezone.utc)


def run(id, minutes, event="schedule", status="completed", conclusion="failure"):
    return {
        "id": id,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "created_at": (NOW - timedelta(minutes=minutes)).isoformat(),
        "path": ".github/workflows/research.yml",
    }


class Response:
    def __init__(self, payload=None, code=200):
        self.payload = payload
        self.status_code = code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("API unavailable")

    def json(self):
        return self.payload


class PublicationSafetyTests(unittest.TestCase):
    def test_waiting_paper_and_research_refresh_main_before_processing(self):
        groups = []
        for filename in ("research.yml", "simulate.yml"):
            text = Path(".github/workflows", filename).read_text(encoding="utf-8")
            self.assertIn("git fetch --no-tags origin main", text)
            self.assertIn("git checkout -B main origin/main", text)
            self.assertIn('test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"', text)
            self.assertLess(text.index("git checkout -B main origin/main"),
                            text.index("actions/setup-python@v5"))
            self.assertIn("cancel-in-progress: false", text)
            self.assertNotIn("git push --force", text)
            self.assertNotIn("git reset --hard origin/main\n", text[text.index("Save paper portfolios"):]
                             if filename == "simulate.yml" else
                             text[text.index("Publish research observations"):])
            self.assertIn("group: seiko-trading-lab-serialized", text)
            groups.append("seiko-trading-lab-serialized")
        self.assertEqual(len(groups), 2)

    def test_conflict_only_retry_is_qualified_and_authorized(self):
        text = Path(".github/workflows/research.yml").read_text(encoding="utf-8")
        self.assertIn("  actions: write", text)
        self.assertIn("id: publication", text)
        self.assertIn('echo "retry_needed=true" >> "$GITHUB_OUTPUT"', text)
        self.assertIn("steps.publication.outputs.retry_needed == 'true'", text)
        self.assertIn("run: python -m research.publication_recovery", text)

    def test_original_failed_schedule_with_only_older_success_retries(self):
        self.assertTrue(recovery.should_recover([
            run(12, 5), run(11, 15, conclusion="success")
        ], 12, NOW))

    def test_newer_run_blocks_retry_even_if_it_failed(self):
        for newer_status in ("queued", "in_progress", "completed"):
            self.assertFalse(recovery.should_recover([
                run(12, 5), run(13, 2, status=newer_status)
            ], 12, NOW))

    def test_prior_dispatch_or_self_dispatch_prevents_retry_storm(self):
        self.assertFalse(recovery.should_recover([
            run(12, 5), run(11, 45, event="workflow_dispatch")
        ], 12, NOW))
        self.assertFalse(recovery.should_recover([
            run(12, 5, event="workflow_dispatch")
        ], 12, NOW))

    def test_stale_or_unverifiable_run_fails_closed(self):
        self.assertFalse(recovery.should_recover([], 12, NOW))
        self.assertFalse(recovery.should_recover([run(12, 130)], 12, NOW))
        self.assertFalse(recovery.should_recover([run(11, 5)], 12, NOW))
        self.assertFalse(recovery.should_recover([
            run(12, 5), {"id": 11, "created_at": "bad", "path": ".github/workflows/research.yml"}
        ], 12, NOW))
        self.assertFalse(recovery.should_recover([run(i, 3) for i in range(100)], 12, NOW))

    def test_only_one_api_dispatch_for_legitimate_race(self):
        now = datetime.now(timezone.utc)
        def at(id, minutes, event="schedule", conclusion="failure"):
            return {
                "id": id, "event": event, "conclusion": conclusion,
                "created_at": (now - timedelta(minutes=minutes)).isoformat(),
                "path": ".github/workflows/research.yml",
            }
        posts = []
        def get(url, **kwargs):
            self.assertTrue(url.endswith("/actions/workflows/research.yml/runs"))
            self.assertNotIn("fake-token", str(kwargs.get("params")))
            return Response({"workflow_runs": [at(42, 3), at(41, 20, conclusion="success")]})
        def post(url, **kwargs):
            posts.append((url, kwargs))
            return Response({}, 204)
        env = {"GITHUB_REPOSITORY": recovery.REPOSITORY, "GITHUB_RUN_ID": "42",
               "GITHUB_EVENT_NAME": "schedule", "GH_TOKEN": "fake-token"}
        with patch.dict(os.environ, env):
            result = recovery.recover(get=get, post=post)
        self.assertIn("dispatched", result)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][1]["json"], {"ref": "main"})

    def test_unauthorized_or_api_error_never_dispatches(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("network must not be called")
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": "someone/else",
            "GITHUB_RUN_ID": "42", "GITHUB_EVENT_NAME": "schedule",
            "GH_TOKEN": "fake-token"}):
            self.assertIn("skipped", recovery.recover(get=forbidden, post=forbidden))
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": recovery.REPOSITORY,
            "GITHUB_RUN_ID": "42", "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GH_TOKEN": "fake-token"}):
            self.assertIn("skipped", recovery.recover(get=forbidden, post=forbidden))
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": recovery.REPOSITORY,
            "GITHUB_RUN_ID": "42", "GITHUB_EVENT_NAME": "schedule",
            "GH_TOKEN": "fake-token"}):
            self.assertIn("skipped", recovery.recover(
                get=lambda *a, **k: Response(code=403), post=forbidden))


if __name__ == "__main__":
    unittest.main()
