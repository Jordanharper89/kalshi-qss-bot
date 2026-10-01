
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.six_dex_subscription_plan import *
class T(unittest.TestCase):
    def test_processed_account_subscribe(self):
        s=[Subscription("RAYDIUM_CPMM","P","A"),Subscription("ORCA","Q","B")]
        r=requests(s);self.assertEqual(len(r),2)
        self.assertTrue(all(x["method"]=="accountSubscribe" for x in r))
        self.assertTrue(all(x["params"][1]["commitment"]=="processed" for x in r))
        print("[PASS] six-DEX exact-role accounts compile to processed accountSubscribe requests")
if __name__=="__main__": unittest.main(verbosity=2)
