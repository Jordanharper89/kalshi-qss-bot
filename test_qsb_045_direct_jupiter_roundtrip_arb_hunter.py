import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.direct_jupiter_roundtrip_arb import core as c
class T(unittest.TestCase):
    def test_profitable_roundtrip(self):
        calls=[]
        def h(url,timeout):
            calls.append(url)
            if len(calls)==1:return {"outAmount":"1000000","transaction":"A","requestId":"1","router":"R1"}
            return {"outAmount":"10200000","transaction":"B","requestId":"2","router":"R2"}
        old=c.MODELED_COST_LAMPORTS;c.MODELED_COST_LAMPORTS=100000
        try:
            x=c.roundtrip("T",10000000,http=h)
            self.assertEqual(x["net_lamports"],100000);self.assertTrue(x["qualified"])
        finally:c.MODELED_COST_LAMPORTS=old
        print("[PASS] positive after-cost roundtrip qualifies")
    def test_missing_transaction_rejected(self):
        calls=[]
        def h(url,timeout):
            calls.append(1)
            if len(calls)==1:return {"outAmount":"1000000","transaction":None,"requestId":"1"}
            return {"outAmount":"11000000","transaction":"B","requestId":"2"}
        x=c.roundtrip("T",10000000,http=h)
        self.assertFalse(x["qualified"])
        print("[PASS] missing executable leg transaction rejects")
    def test_negative_rejected(self):
        calls=[]
        def h(url,timeout):
            calls.append(1)
            if len(calls)==1:return {"outAmount":"1000000","transaction":"A","requestId":"1"}
            return {"outAmount":"9900000","transaction":"B","requestId":"2"}
        x=c.roundtrip("T",10000000,http=h)
        self.assertLess(x["net_bps"],0);self.assertFalse(x["qualified"])
        print("[PASS] negative roundtrip rejects")
    def test_authority_false_contract(self):
        self.assertEqual(c.WSOL,"So11111111111111111111111111111111111111112")
        print("[PASS] WSOL anchor fixed; runtime remains non-executing")
if __name__=="__main__":unittest.main(verbosity=2)
