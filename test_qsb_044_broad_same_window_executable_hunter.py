import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_broad_same_window import live
WSOL=live.WSOL

def tx_token_token():
    return {"slot":10,"meta":{"err":None,"fee":5000,"preBalances":[10000000000],"postBalances":[9999995000],
      "preTokenBalances":[{"owner":"W","mint":"A","uiTokenAmount":{"uiAmountString":"2"}},{"owner":"W","mint":"B","uiTokenAmount":{"uiAmountString":"1"}}],
      "postTokenBalances":[{"owner":"W","mint":"A","uiTokenAmount":{"uiAmountString":"1"}},{"owner":"W","mint":"B","uiTokenAmount":{"uiAmountString":"4"}}]},
      "transaction":{"message":{"accountKeys":[{"pubkey":"W","signer":True}]}}}

def tx_sol_buy():
    return {"slot":11,"meta":{"err":None,"fee":5000,"preBalances":[2000000000],"postBalances":[1499995000],
      "preTokenBalances":[{"owner":"W","mint":"T","uiTokenAmount":{"uiAmountString":"0"}}],
      "postTokenBalances":[{"owner":"W","mint":"T","uiTokenAmount":{"uiAmountString":"100"}}]},
      "transaction":{"message":{"accountKeys":[{"pubkey":"W","signer":True}]}}}

class T(unittest.TestCase):
    def test_exact_token_token(self):
        x=live.economic_from_tx("S","ORCA",10,tx_token_token())
        self.assertEqual(x["discovery_quality"],"EXACT_TOKEN_TOKEN")
        self.assertEqual((x["input_mint"],x["output_mint"]),("A","B"))
        print("[PASS] exact token-token discovery preserved")
    def test_native_sol_buy(self):
        x=live.economic_from_tx("S","METEORA_DLMM",11,tx_sol_buy())
        self.assertEqual(x["input_mint"],WSOL);self.assertEqual(x["output_mint"],"T")
        self.assertAlmostEqual(x["input_amount"],.5,places=9)
        self.assertEqual(x["discovery_quality"],"REQUOTE_REQUIRED")
        print("[PASS] native SOL -> token discovery recovered and marked requote-required")
    def test_multivenue_rejected(self):
        rs=[{"signature":"S","venue":"ORCA","slot":1},{"signature":"S","venue":"RAYDIUM_CLMM","slot":1}]
        self.assertFalse(live.select_signatures(rs))
        print("[PASS] multi-venue attribution remains rejected")
    def test_batch_hydration(self):
        sel=[("S","ORCA",10)]
        def b(reqs):return {1:tx_token_token()}
        d=live.hydrate_selected(sel,b);self.assertIn("S",d)
        print("[PASS] batched transaction hydration contract")
if __name__=="__main__":unittest.main(verbosity=2)
