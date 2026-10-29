"""Duplicate GitHub schedules must not double-execute one portfolio snapshot."""
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from research.paper_cycle_guard import due

class PaperCycleGuardTest(unittest.TestCase):
    def test_previous_completed_cycle_prevents_duplicate_dispatch(self):
        now=datetime(2026,10,29,1,5,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"state.json"
            p.write_text(json.dumps({"updated":(now-timedelta(seconds=110)).isoformat()}))
            self.assertFalse(due(p,now))
            self.assertTrue(due(p,now+timedelta(seconds=190)))
            p.write_text('{"updated":"not-a-date"}')
            self.assertTrue(due(p,now))
    def test_missing_state_does_not_block_recovery(self):
        self.assertTrue(due("/unavailable/state.json"))
if __name__=="__main__":
    unittest.main()
