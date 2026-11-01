"""Health: latest successful GitHub run supersedes old failed emails."""
import unittest
from datetime import datetime,timezone
from research import ops_status as ops

NOW=datetime(2026,10,29,0,0,tzinfo=timezone.utc)
class R:
    def raise_for_status(self):pass
    def json(self):
        return {"workflow_runs":[
          {"name":"Paper trading","status":"completed","conclusion":"failure",
           "id":22,"created_at":"2026-10-28T22:00:00Z"},
          {"name":"Paper trading","status":"completed","conclusion":"success",
           "id":23,"created_at":"2026-10-28T23:00:00Z",
           "html_url":"https://github.com/test/actions/runs/23"},
          {"name":"Seiko research — guarded automatic analysis","status":"completed",
           "conclusion":"success","id":24,"created_at":"2026-10-28T23:10:00Z"}
        ]}

class Tests(unittest.TestCase):
    def test_newer_success_makes_previous_red_email_historical(self):
        out=ops.workflows(get=lambda *a,**k:R())
        self.assertEqual(out["workflows"]["Paper trading"]["state"],"healthy")
        self.assertEqual(out["workflows"]["Paper trading"]["run_id"],23)
    def test_newer_running_recovery_suppresses_stale_failed_run(self):
        class Recovery:
            def raise_for_status(self):pass
            def json(self):
                return {"workflow_runs":[
                  {"name":"Seiko research — guarded automatic analysis",
                   "status":"completed","conclusion":"failure",
                   "id":11,"created_at":"2026-10-29T08:44:26Z"},
                  {"name":"Seiko research — guarded automatic analysis",
                   "status":"in_progress","conclusion":None,
                   "id":12,"created_at":"2026-10-29T08:54:26Z"}
                ]}
        result=ops.workflows(get=lambda *a,**k:Recovery())
        latest=result["workflows"]["Seiko research — guarded automatic analysis"]
        self.assertEqual(latest["state"],"running")
        self.assertEqual(latest["run_id"],12)

    def test_crowded_repo_feed_cannot_hide_a_recent_research_success(self):
        """Each API request is scoped to the actual workflow file."""
        requested=[]
        class ScopedResponse:
            def __init__(self, name):self.name=name
            def raise_for_status(self):pass
            def json(self):
                return {"workflow_runs":[{
                    "name":self.name,"status":"completed","conclusion":"success",
                    "id":91 if self.name=="Paper trading" else 92,
                    "created_at":"2026-11-01T11:46:25Z"}]}
        def get(url,**kwargs):
            requested.append((url,kwargs["params"]["per_page"]))
            name=("Paper trading" if "/simulate.yml/" in url else
                  "Seiko research — guarded automatic analysis")
            return ScopedResponse(name)
        out=ops.workflows(get=get)
        self.assertEqual(out["state"],"available")
        self.assertEqual(out["workflows"]["Seiko research — guarded automatic analysis"]["run_id"],92)
        self.assertEqual(len(requested),2)
        self.assertTrue(any("/workflows/research.yml/runs" in url for url,_ in requested))
        self.assertTrue(any("/workflows/simulate.yml/runs" in url for url,_ in requested))
        self.assertFalse(any(url.endswith("/actions/runs") for url,_ in requested))

    def test_one_workflow_api_failure_does_not_erase_the_other_status(self):
        class PaperResponse:
            def raise_for_status(self):pass
            def json(self):
                return {"workflow_runs":[{"name":"Paper trading",
                        "status":"completed","conclusion":"success","id":81,
                        "created_at":"2026-11-01T12:00:00Z"}]}
        def get(url,**kwargs):
            if "/research.yml/" in url:raise ops.requests.RequestException("temporary")
            return PaperResponse()
        out=ops.workflows(get=get)
        self.assertEqual(out["state"],"partial")
        self.assertEqual(out["workflows"]["Paper trading"]["state"],"healthy")
        self.assertEqual(out["workflows"]["Seiko research — guarded automatic analysis"]["state"],"unknown")

    def test_status_is_honest_about_partial_whale_monitor(self):
        data={
          "evolution":{"counts":{"tracked":36,"testing":3,"activated":0}},
          "model":{"generated_at":NOW.isoformat(),"state":"model_reflection_completed"},
          "intraday":{"generated_at":NOW.isoformat(),"assets":{"BTCUSD":{},"ETHUSD":{}}},
          "transfers":{"state":"observing"},
          "experiments":{"schema":1,"active":4},
          "news":{"status":"available"},
        }
        output=ops.build(NOW,data,{"state":"available","workflows":{
            "Paper trading":{"state":"healthy"},
            "Seiko research — guarded automatic analysis":{"state":"healthy"}}})
        roles={x["id"]:x for x in output["roadmap"]}
        self.assertEqual(roles["scenarios"]["status"],"active")
        self.assertEqual(roles["whales"]["status"],"partial")
        self.assertEqual(roles["real"]["status"],"disabled")
        self.assertFalse(output["real_orders"])
    def test_true_recent_failure_is_alerted(self):
        output=ops.build(NOW,{},{"state":"available","workflows":{
            "Paper trading":{"state":"failure","run_id":88}}})
        self.assertIn("88"," ".join(output["alerts"]))
        self.assertEqual(output["status"],"needs_attention")

if __name__=="__main__":unittest.main()
