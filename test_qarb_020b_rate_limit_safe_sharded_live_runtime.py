import asyncio,unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.six_dex_live_stream import shard_subscriptions,aggregate

class T(unittest.TestCase):
    def test_256_accounts_split_under_working_single_connection_count(self):
        subs=[SimpleNamespace(venue="V",pool="P",account=str(i)) for i in range(256)]
        shards=shard_subscriptions(subs,48)
        self.assertEqual(len(shards),6)
        self.assertTrue(all(len(x)<=48 for x in shards))
        self.assertEqual(sum(map(len,shards)),256)
        print("[PASS] 256 accounts -> six connections, max 48 subscriptions each")

    def test_repo_proven_98_accounts_are_not_forced_into_one_new_connection(self):
        subs=[SimpleNamespace(venue="V",pool="P",account=str(i)) for i in range(98)]
        shards=shard_subscriptions(subs,48)
        self.assertEqual([len(x) for x in shards],[48,48,2])
        print("[PASS] 98-account proven workload is conservatively sharded 48/48/2")

    def test_aggregate(self):
        r=aggregate([
          {"subscriptions":48,"acks":48,"notifications":3,"venues":{"A":3},"connected":True,"rate_limited":False,"error":None,"dispatch_ms":[.1,.2]},
          {"subscriptions":20,"acks":20,"notifications":4,"venues":{"B":4},"connected":True,"rate_limited":False,"error":None,"dispatch_ms":[.3]},
        ])
        self.assertEqual(r["subscriptions"],68);self.assertEqual(r["notifications"],7)
        self.assertEqual(r["successful_connections"],2);self.assertEqual(r["rate_limited_connections"],0)
        self.assertEqual(r["venues"],{"A":3,"B":4})
        print("[PASS] shard results aggregate without losing venue counts")

    def test_rate_limit_truth_preserved(self):
        r=aggregate([{"subscriptions":48,"acks":0,"notifications":0,"venues":{},"connected":True,
                      "rate_limited":True,"error":"1013 rate limit","dispatch_ms":[]}])
        self.assertEqual(r["rate_limited_connections"],1)
        self.assertTrue(r["errors"])
        print("[PASS] 1013 remains visible instead of crashing or being hidden")

if __name__=="__main__":
    unittest.main(verbosity=2)
