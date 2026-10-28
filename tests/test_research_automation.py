"""Safety tests for autonomous research."""
import unittest
from datetime import datetime, timezone
from research import auto_research as ar

def sample(kind, days=0.1, cycles=0):
    rows=[]
    for index in range(18):
        row={"strategy":f"asset_{index}","asset":"BTCUSD","capital_usd":19.5,
             "return_pct":-2.5,"max_observed_drawdown_pct":3}
        if kind=="crypto":
            row.update(completed_roundtrips=cycles if index==0 else 0,
                       fees_paid_usd=.15,observation_count=5)
        else:
            row.update(closed_roundtrips=cycles if index==0 else 0,fees_usd=.02,
                       observations=5,pricing_quality="OBSERVED")
        rows.append(row)
    return {"model":"realistic_v2" if kind=="crypto" else "multi_asset_micro_v2",
            "elapsed_days":days,"started_at":"2026-10-28T18:00:00Z",
            "updated_at":"2026-10-29T18:00:00Z",
            "latest_total_usd":351,"capital_usd":351,"strategies":rows}

class ResearchAutomationTests(unittest.TestCase):
    def test_new_data_does_not_get_promoted(self):
        t=datetime.now(timezone.utc)
        r=ar.build_report(sample("crypto"),sample("multi"),t)
        self.assertEqual(r["qualification"]["ready_for_human_review"],0)
        self.assertEqual(r["qualification"]["proven_profitable"],0)
        self.assertFalse(r["real_trading_enabled"])
        self.assertFalse(r["autonomous_strategy_changes_enabled"])
        self.assertEqual(r["labs"]["crypto"]["initial_usd"],360)
        self.assertEqual(r["labs"]["multi"]["initial_usd"],360)

    def test_review_gates_are_not_profit_claims(self):
        t=datetime.now(timezone.utc)
        r=ar.build_report(sample("crypto",20,25),sample("multi",40,25),t)
        self.assertEqual(r["qualification"]["ready_for_human_review"],2)
        self.assertEqual(r["qualification"]["proven_profitable"],0)

    def test_incomplete_data_is_not_invented(self):
        t=datetime.now(timezone.utc)
        r=ar.build_report({},None,t)
        self.assertEqual(r["labs"]["crypto"]["state"],"invalid_source")
        self.assertEqual(r["labs"]["multi"]["state"],"source_missing")
        self.assertEqual(r["qualification"]["ready_for_human_review"],0)

if __name__=="__main__":
    unittest.main()
