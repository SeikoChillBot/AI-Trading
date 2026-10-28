"""Offline tests for free market pulse and public stablecoin sampling."""
import unittest
from datetime import datetime, timezone
from research import large_transfers as chain, market_pulse as pulse

NOW = datetime(2026, 10, 28, 22, 0, tzinfo=timezone.utc)
TX = "0x" + "b"*64
A, B = "0x"+"1"*40, "0x"+"2"*40

def tx(token, units="2100000000000", contract=None):
    return {"token":{"address_hash":contract or chain.CONTRACTS[token]},
            "total":{"decimals":"6","value":units},
            "timestamp":"2026-10-28T21:00:00Z","tx_hash":TX,
            "from":{"hash":A},"to":{"hash":B},"log_index":21}

class Response:
    def __init__(self, data): self.data=data
    def raise_for_status(self): pass
    def json(self): return self.data

class PublicTransferTests(unittest.TestCase):
    def test_baseline_and_new_transfer(self):
        pages = {t:[tx(t)] for t in chain.CONTRACTS}
        def get(url, **kw):
            t = "USDC" if chain.CONTRACTS["USDC"] in url else "USDT"
            return Response({"items":pages[t]})
        first, state = chain.build(NOW, {}, get)
        self.assertEqual(first["large_transfers_observed"],2)
        self.assertEqual(first["large_transfers_new"],[])
        self.assertFalse(first["buy_sell_inference"])
        repeat,_ = chain.build(NOW,state,get)
        self.assertEqual(repeat["large_transfers_new"],[])
        pages["USDC"]=[tx("USDC","3200000000000")]
        changed,_=chain.build(NOW,state,get)
        self.assertEqual(len(changed["large_transfers_new"]),1)
        self.assertEqual(changed["large_transfers_new"][0]["trade_inference"],"unknown")

    def test_spoofed_contract_and_failure(self):
        with self.assertRaises(ValueError):
            chain.transfer(tx("USDC",contract=chain.CONTRACTS["USDT"]),"USDC",NOW)
        with self.assertRaises(ValueError):
            chain.transfer(tx("USDC","NaN"),"USDC",NOW)
        def unavailable(*a,**kw): raise chain.requests.ConnectionError("offline")
        old={"initialized":True,"seen_ids":["a"]}
        report,state=chain.build(NOW,old,unavailable)
        self.assertEqual(report["state"],"unavailable")
        self.assertEqual(state,old)

class PulseTests(unittest.TestCase):
    def test_descriptive_only(self):
        bars={"BTCUSD":[{"t":int(NOW.timestamp())-(32-i)*86400,
                         "close":100+i} for i in range(32)]}
        context={"model":"market_context_observation_v1",
                 "generated_at":NOW.isoformat(),"errors":{},
                 "observations":{"sentiment":{"index":43}}}
        whales={"generated_at":NOW.isoformat(),"state":"observing",
                "large_transfers_observed":2,"large_transfers_new":[{"id":"a"}],
                "sample_highlights":[{"nominal_usd_approx":2000000}]}
        result=pulse.build(NOW,bars,context,whales)
        self.assertEqual(result["assets"]["BTCUSD"]["direction_7d"],"up")
        self.assertEqual(result["large_transfers"]["new_in_sample"],1)
        self.assertEqual(result["macro"]["fear_greed_index"],43)
        self.assertFalse(result["real_orders"])
        self.assertEqual(result["signal_count"],0)
        self.assertNotIn("ETHUSD",result["assets"])

if __name__=="__main__":unittest.main()
