import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_same_window_hydration import live

def tx(slot=100):
    return {"slot":slot,"meta":{"err":None,
      "preTokenBalances":[
        {"owner":"W","mint":"A","uiTokenAmount":{"uiAmountString":"2.0"}},
        {"owner":"W","mint":"B","uiTokenAmount":{"uiAmountString":"5.0"}}],
      "postTokenBalances":[
        {"owner":"W","mint":"A","uiTokenAmount":{"uiAmountString":"1.0"}},
        {"owner":"W","mint":"B","uiTokenAmount":{"uiAmountString":"8.0"}}]},
      "transaction":{"message":{"accountKeys":[{"pubkey":"W","signer":True}]}}}

class T(unittest.TestCase):
    def test_exact_delta(self):
        x=live.economic_from_tx("S","ORCA",100,tx())
        self.assertEqual((x["input_mint"],x["output_mint"]),("A","B"))
        self.assertEqual((x["input_amount"],x["output_amount"]),(1.0,3.0))
        print("[PASS] exact single-venue signer token deltas become economics")
    def test_multivenue_signature_rejected_at_selection(self):
        rs=[{"signature":"S","venue":"ORCA","slot":1},{"signature":"S","venue":"METEORA_DLMM","slot":1}]
        self.assertEqual(live.select_signatures(rs),[])
        print("[PASS] multi-venue transaction cannot be falsely attributed to one venue")
    def test_per_venue_selection(self):
        rs=[{"signature":"A","venue":"ORCA","slot":2},{"signature":"B","venue":"RAYDIUM_CLMM","slot":3}]
        xs=live.select_signatures(rs);self.assertEqual({x[1] for x in xs},{"ORCA","RAYDIUM_CLMM"})
        print("[PASS] current-window selection covers distinct non-Pump venues")
    def test_hydrate(self):
        rs=[{"signature":"A","venue":"ORCA","slot":100}]
        d=live.hydrate(rs,lambda m,p:tx())
        self.assertEqual(d["exact"]["ORCA"],1);self.assertFalse(d["rows"][0]["execution_authority"])
        print("[PASS] hydration remains read-only")
if __name__=="__main__":unittest.main(verbosity=2)
