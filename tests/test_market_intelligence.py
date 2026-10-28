"""Offline validation for source-tagged market context and wallet transfers."""
import unittest
from datetime import datetime,timezone
from research import market_context as market
from research import whale_watch as whales

NOW=datetime(2026,10,28,22,0,tzinfo=timezone.utc)
WALLET="0x"+"1"*40
CONTRACT="0x"+"a"*40
COUNTERPARTY="0x"+"2"*40
TX="0x"+"b"*64

class FakeResponse:
    def __init__(self,value):self.value=value
    def raise_for_status(self):pass
    def json(self):return self.value

class MarketTests(unittest.TestCase):
    def test_context_labels_never_trigger_trade(self):
        fake={
            market.SOURCES["sentiment"]:{"data":[{
               "value":"42","timestamp":str(int(NOW.timestamp()-3600)),
               "value_classification":"Fear"}]},
            market.SOURCES["chain_tvl"]:[
               {"name":"Ethereum","tvl":20000000000},
               {"name":"Solana","tvl":9000000000}],
            market.SOURCES["stablecoins"]:{"peggedAssets":[
               {"circulating":{"peggedUSD":30000000000}} for _ in range(5)]}
        }
        result=market.build(NOW,lambda url,**kwargs:FakeResponse(fake[url]))
        self.assertEqual(len(result["observations"]),3)
        self.assertEqual(result["errors"],{})
        self.assertFalse(result["auto_trading"])
        self.assertFalse(result["whale_purchases_inferred"])
        self.assertEqual(result["observations"]["sentiment"]["index"],42)

    def test_stale_sentiment_and_invalid_missing_chains_fail_closed(self):
        with self.assertRaises(ValueError):
            market.fear_greed({"data":[{"value":"80",
                "timestamp":str(int(NOW.timestamp()-7*86400))}]},NOW)
        with self.assertRaises(ValueError):
            market.chain_tvl([{"name":"Ethereum","tvl":2}])

class WhaleTests(unittest.TestCase):
    def setUp(self):
        self.watch={"schema":1,"wallets":[{
            "chainid":1,"address":WALLET,"label":"Verified example",
            "source_url":"https://example.com/source"}]}
        self.tx={"hash":TX,"from":COUNTERPARTY,"to":WALLET,
            "contractAddress":CONTRACT,"tokenDecimal":"6",
            "tokenSymbol":"USDC","value":"12000000",
            "timeStamp":str(int(NOW.timestamp()-60))}

    def test_empty_or_keyless_does_not_query_private_service(self):
        result,_=whales.build(NOW,"",self.watch,{"addresses":{}},
            lambda *args,**kwargs: self.fail("Network must not be contacted"))
        self.assertEqual(result["state"],"not_configured")
        self.assertEqual(result["new_transfer_events"],[])

    def test_unverified_labels_cannot_be_silently_used(self):
        entry={"schema":1,"wallets":[{"address":WALLET,"label":"Guess",
            "chainid":1}]}
        with self.assertRaises(ValueError):whales.validate_watchlist(entry)

    def test_first_poll_baselines_and_second_reports_transfer_only(self):
        responses=[[self.tx],[self.tx,dict(self.tx,hash="0x"+"c"*64)]]
        cursor={"i":0}
        def get(*args,**kwargs):
            answer=responses[cursor["i"]];cursor["i"]+=1
            return FakeResponse({"status":"1","result":answer})
        before={"schema":1,"addresses":{}}
        first,state=whales.build(NOW,"dummy",self.watch,before,get)
        self.assertEqual(first["new_transfer_events"],[])
        second,state=whales.build(NOW,"dummy",self.watch,state,get)
        self.assertEqual(len(second["new_transfer_events"]),1)
        event=second["new_transfer_events"][0]
        self.assertEqual(event["quantity"],"12")
        self.assertEqual(event["trade_inference"],"unknown")
        self.assertEqual(event["classification"],
                         "ERC20_TRANSFER_ONLY_NOT_A_TRADE")
        self.assertIsNone(event["usd_value"])

if __name__=="__main__":
    unittest.main()
