import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025_real_atomic_simulation as q

class FakeTx:
    def __bytes__(self):
        return b"x"*900

class T(unittest.TestCase):
    def test_execution_false(self):
        self.assertIs(q.execution_authority,False)
        print("[PASS] execution_authority=FALSE")

    def test_packet_guard(self):
        class Big:
            def __bytes__(self): return b"x"*1233
        r=q.simulate(Big(),q.Pubkey.default())
        self.assertEqual(r["reason"],"ATOMIC_TX_TOO_LARGE")
        print("[PASS] >1232 bytes cannot reach simulateTransaction")

    def test_real_sim_parser(self):
        calls=[]
        def fake_rpc(method,params):
            calls.append(method)
            if method=="getBalance":
                return {"value":1000000000}
            if method=="simulateTransaction":
                return {"value":{"err":None,"accounts":[{"lamports":1000500000}],"logs":["ok"],"unitsConsumed":123456}}
            raise AssertionError(method)
        with patch.object(q,"rpc",fake_rpc):
            r=q.simulate(FakeTx(),q.Pubkey.default())
        self.assertEqual(calls,["getBalance","simulateTransaction"])
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["net_sol"],0.0005)
        print("[PASS] real simulateTransaction response -> payer balance delta PNL")

    def test_confirmed_blockhash(self):
        seen={}
        def fake_rpc(method,params):
            seen["method"]=method;seen["params"]=params
            return {"value":{"blockhash":"11111111111111111111111111111111"}}
        with patch.object(q,"rpc",fake_rpc):
            q.blockhash()
        self.assertEqual(seen["method"],"getLatestBlockhash")
        self.assertEqual(seen["params"][0]["commitment"],"confirmed")
        print("[PASS] current confirmed blockhash used")

if __name__=="__main__":
    unittest.main(verbosity=2)
