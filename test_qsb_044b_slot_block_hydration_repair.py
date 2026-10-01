import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_broad_same_window import live
WSOL=live.WSOL

def block_tx(sig="S"):
    return {"transaction":{"signatures":[sig],"message":{"accountKeys":[{"pubkey":"W","signer":True}]}},
            "meta":{"err":None,"fee":5000,"preBalances":[2000000000],"postBalances":[1499995000],
                    "preTokenBalances":[{"owner":"W","mint":"T","uiTokenAmount":{"uiAmountString":"0"}}],
                    "postTokenBalances":[{"owner":"W","mint":"T","uiTokenAmount":{"uiAmountString":"100"}}]}}

class T(unittest.TestCase):
    def test_block_hydrates_many_without_gettransaction(self):
        sel=[("S1","ORCA",10),("S2","RAYDIUM_CLMM",10)]
        def rpc(method,params):
            self.assertEqual(method,"getBlock")
            return {"transactions":[block_tx("S1"),block_tx("S2")]}
        got,meta=live.hydrate_selected(sel,rpc)
        self.assertEqual(set(got),{"S1","S2"});self.assertEqual(meta["slot_count"],1)
        print("[PASS] one block RPC hydrates multiple selected signatures")
    def test_native_sol_discovery(self):
        x=dict(block_tx("S"));x["slot"]=10
        e=live.economic_from_tx("S","ORCA",10,x)
        self.assertEqual(e["input_mint"],WSOL);self.assertEqual(e["discovery_quality"],"REQUOTE_REQUIRED")
        print("[PASS] native SOL route discovery preserved")
    def test_multivenue_signature_still_rejected(self):
        rs=[{"signature":"S","venue":"ORCA","slot":10},{"signature":"S","venue":"METEORA_DLMM","slot":10}]
        self.assertFalse(live.select_signatures(rs))
        print("[PASS] multi-venue attribution guard preserved")
    def test_slot_cap(self):
        sel=[(f"S{i}","ORCA",100-i) for i in range(12)]
        calls=[]
        def rpc(method,params):
            calls.append(params[0]);return {"transactions":[]}
        _,m=live.hydrate_selected(sel,rpc)
        self.assertLessEqual(m["slot_count"],live.MAX_SLOTS)
        print("[PASS] bounded slot-block RPC fanout")
if __name__=="__main__":unittest.main(verbosity=2)
