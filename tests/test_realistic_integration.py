"""End-to-end offline audit: 18 positions begin together, no real orders."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import realistic_sim as sim

BOOK = {"asks":[(100.2,10.0)],"bids":[(100.0,10.0)],"spread_pct":0.1998}
META = {"min_base":0.01,"min_cost_usd":0.5,"lot_decimals":6}

class WorkflowTests(unittest.TestCase):
    def test_synchronized_start_and_rejected_orders(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            files={"STATE":base/"state.json","LATEST":base/"latest.csv",
                   "HISTORY":base/"history.csv","ORDERS":base/"orders.csv"}
            patches=[patch.object(sim,k,v) for k,v in files.items()]
            patches.extend([
                patch.object(sim,"fetch_candles",side_effect=lambda s,i: [(1700000000000-(40-n)*i*60000,100.0) for n in range(40)]),
                patch.object(sim,"pair_metadata",return_value={s:dict(META) for s in sim.PAIRS}),
                patch.object(sim,"orderbook",return_value=dict(BOOK)),
                patch.object(sim,"decide",side_effect=lambda mode,prices,holding,p,scale: "buy" if mode=="hold" else "wait")
            ])
            import contextlib
            with contextlib.ExitStack() as stack:
                for p in patches:stack.enter_context(p)
                # Freeze clock proximity: synthetic candle dates are deliberately old,
                # so test only the pure execution system here, not market freshness.
                with patch.object(sim,"datetime") as clock:
                    from datetime import datetime,timezone
                    clock.now.return_value=datetime.fromtimestamp(1700000000000/1000,timezone.utc)
                    clock.fromtimestamp.side_effect=datetime.fromtimestamp
                    sim.main()
                rows=list(csv.DictReader(files["LATEST"].open(newline="")))
                self.assertEqual(len(rows),18)
                state=json.loads(files["STATE"].read_text())
                self.assertEqual(len(state["portfolios"]),18)
                self.assertEqual({row["position"] for row in rows if row["strategy"].endswith("_hold")},{"CRYPTO"})
                events=list(csv.DictReader(files["ORDERS"].open(newline="")))
                self.assertEqual(len(events),3)
                self.assertTrue(all(e["status"]=="FILLED_SIMULATED" for e in events))
                self.assertEqual(len({e["observed_at"] for e in events}),1)
                self.assertEqual(len(list(csv.DictReader(files["HISTORY"].open(newline="")))),18)

if __name__=="__main__":
    unittest.main()
