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
        result=base.build(NOW,fail,fail)
        self.assertEqual(result["state"],"unavailable")
        self.assertEqual(result["highlights"],[])
    def test_public_rpc_fallback_decodes_only_native_usdc_transfer(self):
        def explorer(*a,**k):
            raise base.requests.HTTPError("Explorer denied")
        class RpcReply:
            def __init__(self,payload):self.payload=payload
            def raise_for_status(self):pass
            def json(self):return {"jsonrpc":"2.0","id":1,"result":self.payload}
        calls=[]
        def public_rpc(url,**kw):
            self.assertEqual(url,base.RPC)
            args=kw["json"]
            calls.append(args["method"])
            if args["method"]=="eth_blockNumber":
                return RpcReply(hex(1000))
            if args["method"]=="eth_getLogs":
                params=args["params"][0]
                self.assertEqual(params["fromBlock"],hex(989))
                self.assertEqual(params["toBlock"],hex(1000))
                return RpcReply([{
                    "address":base.CONTRACT,
                    "topics":[base.EVENT_TRANSFER,
                              "0x"+"0"*64,"0x"+"0"*64],
                    "transactionHash":HASH,"logIndex":"0x0",
                    "blockNumber":hex(999),
                    "data":hex(3500000*1000000)
                }])
            raise AssertionError("unexpected RPC method")
        report=base.build(NOW,explorer,public_rpc)
        self.assertEqual(calls,["eth_blockNumber","eth_getLogs"])
        self.assertEqual(report["state"],"observing")
        self.assertEqual(report["source_method"],"public_rpc_logs")
        self.assertEqual(report["sampled_blocks"],12)
        self.assertEqual(report["large_count"],1)
        self.assertIsNone(report["highlights"][0]["timestamp"])
        self.assertFalse(report["can_infer_buy_sell"])

    def test_scheduled_mode_uses_free_rpc_without_paid_explorer(self):
        errors=[]
        class RpcReply:
            def __init__(self,data=None,status=200):
                self.data=data
                self.status=status
            def raise_for_status(self):
                if self.status>=400:raise base.requests.HTTPError("blocked")
            def json(self):return {"jsonrpc":"2.0","id":1,"result":self.data}
        def rpc(url,**kw):
            errors.append((url,kw["json"]["method"]))
            if url==base.RPC_HOSTS[0]:return RpcReply(status=429)
            if kw["json"]["method"]=="eth_blockNumber":return RpcReply(hex(1100))
            return RpcReply([])
        def no_explorer(*a,**kw):raise AssertionError("Paid explorer must not be called")
        result=base.build(NOW,get=no_explorer,post=rpc,prefer_rpc=True)
        self.assertEqual(result["state"],"observing")
        self.assertEqual(result["source"],base.RPC_HOSTS[1])
        self.assertEqual(result["sampled_count"],0)
        self.assertEqual(result["large_count"],0)
        self.assertIn("public_rpc_logs",result["source_method"])
        self.assertTrue(all(url!=base.HOST for url,method in errors))

    def test_scheduled_mode_reports_all_endpoint_failures_without_fake_transfers(self):
        def blocked(*args,**kwargs):
            raise base.requests.HTTPError("rate limited")
        report=base.build(NOW,get=blocked,post=blocked,prefer_rpc=True)
        self.assertEqual(report["state"],"unavailable")
        self.assertEqual(report["large_count"],0)
        self.assertEqual(len(report["sources_attempted"]),len(base.RPC_HOSTS))

if __name__=="__main__":
    unittest.main()
