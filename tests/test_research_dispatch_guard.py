"""Isolated watchdog tests; never contact GitHub or send workflow dispatch."""
import os
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from research import research_dispatch_guard as guard

NOW = datetime(2026, 10, 29, 5, 10, tzinfo=timezone.utc)


class Response:
    def __init__(self, data=None, status=200):
        self.data = data
        self.status_code = status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise guard.requests.HTTPError("API unavailable", response=self)
    def json(self):
        return self.data


def run_age(minutes, event="schedule", status="completed"):
    created=(NOW - timedelta(minutes=minutes)).isoformat()
    return {"event":event, "status":status, "created_at":created,
            "name":guard.RESEARCH_NAME,"path":".github/workflows/research.yml"}


class GuardTests(unittest.TestCase):
    def test_recent_scheduled_or_running_prevents_dispatch(self):
        for status in ("completed", "queued", "in_progress"):
            self.assertFalse(guard.should_dispatch(NOW, [run_age(20, status=status)]))
        self.assertFalse(guard.should_dispatch(NOW, [run_age(200), run_age(5, status="queued")]))
        self.assertFalse(guard.should_dispatch(NOW, []))
        self.assertFalse(guard.should_dispatch(NOW, [{}]))

    def test_stale_schedules_dispatch_once(self):
        calls=[]
        def get(url,**kw):
            self.assertTrue(url.endswith("/actions/runs"))
            self.assertNotIn("dummy-test-secret",str(kw.get("params")))
            return Response({"workflow_runs":[run_age(290),run_age(400)]})
        def post(url,**kw):
            calls.append((url,kw))
            return Response({},204)
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":guard.OWNER_REPO}):
            result=guard.check_and_dispatch(NOW,"dummy-test-secret",get,post)
        self.assertIn("dispatched",result)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][1]["json"],{"ref":"main"})
        self.assertIn("/dispatches",calls[0][0])

    def test_recent_dispatch_blocks_duplicate(self):
        posts=[]
        def get(*a,**kw):
            return Response({"workflow_runs":[run_age(200),run_age(4,event="workflow_dispatch",status="queued")]})
        def post(*a,**kw):
            posts.append(1)
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":guard.OWNER_REPO}):
            result=guard.check_and_dispatch(NOW,"fake-secret",get,post)
        self.assertIn("skipped",result)
        self.assertFalse(posts)

    def test_many_unrelated_pages_runs_require_a_complete_time_window(self):
        # With >100 Pages updates inside the threshold, a missing research
        # run might be hidden on page two: never dispatch blindly.
        pages=[{**run_age(20), "name":"pages build and deployment",
                "path":".github/workflows/pages-build-deployment"} for _ in range(100)]
        self.assertFalse(guard.should_dispatch(NOW,pages))
        # Once the 100th newest run is older than the threshold, any recent
        # research run would necessarily have appeared on page one.
        older=[{**run_age(280), "name":"pages build and deployment",
                "path":".github/workflows/pages-build-deployment"} for _ in range(100)]
        self.assertTrue(guard.should_dispatch(NOW,older))

    def test_api_errors_never_dispatch_or_fail_paper(self):
        posts=[]
        def error(*a,**kw):return Response(status=403)
        def post(*a,**kw):posts.append(True)
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":guard.OWNER_REPO}):
            result=guard.check_and_dispatch(NOW,"fake-secret",error,post)
        self.assertIn("skipped",result)
        self.assertFalse(posts)

    def test_missing_token_or_wrong_repository_never_queries_api(self):
        def fails(*a,**kw):raise AssertionError("Network should not be used")
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":"someone/else"}):
            self.assertIn("skipped",guard.check_and_dispatch(NOW,"fake-secret",fails,fails))
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":guard.OWNER_REPO}):
            self.assertIn("skipped",guard.check_and_dispatch(NOW,"",fails,fails))


if __name__=="__main__":
    unittest.main()
