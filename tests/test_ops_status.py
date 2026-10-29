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
