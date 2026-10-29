"""Offline validation of Base USDC sample, without provider calls."""
import unittest
from datetime import datetime, timezone
from research import base_usdc_watch as base

NOW=datetime(2026,10,29,7,0,tzinfo=timezone.utc)
HASH="0x"+"a"*64
class Reply:
    def __init__(self,items):self.items=items
    def raise_for_status(self):pass
    def json(self):return {"items":self.items}

class Tests(unittest.TestCase):
    def test_native_contract_only_and_no_trade_inference(self):
        row={"token":{"address_hash":base.CONTRACT},
             "total":{"decimals":"6","value":"2500000000000"},
             "timestamp":"2026-10-29T06:59:00Z","transaction_hash":HASH}
        result=base.build(NOW,lambda *a,**k:Reply([row]))
        self.assertEqual(result["sampled_count"],1)
        self.assertEqual(result["large_count"],1)
        self.assertFalse(result["can_infer_buy_sell"])
        self.assertFalse(result["real_orders"])
        self.assertEqual(result["highlights"][0]["trade_inference"],"unknown")
        row["token"]["address_hash"]="0x"+"0"*40
        result=base.build(NOW,lambda *a,**k:Reply([row]))
        self.assertEqual(result["large_count"],0)
    def test_source_outage_reported_not_fabricated(self):
        def fail(*a,**k):
            raise base.requests.ConnectionError("test")
        result=base.build(NOW,fail)
        self.assertEqual(result["state"],"unavailable")
        self.assertEqual(result["highlights"],[])
if __name__=="__main__":
    unittest.main()
