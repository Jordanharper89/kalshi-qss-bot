import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_028_mriya_route_decoder as q
class T(unittest.TestCase):
    def test_decode(self):
        p={"target":"W","rows":[{"signature":"s","slot":1,"err":None,"program_ids":[
        "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA","LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"],
        "wallet_token_deltas":{"A":1.0,"B":-2.0},"wallet_sol_delta":0}]}
        r=q.decode(p); self.assertEqual(r["rows"][0]["route_class"],"MULTI_DEX")
        self.assertEqual(r["rows"][0]["economic_shape"],"TOKEN_TO_TOKEN")
        print("[PASS] multi-DEX route and wallet flow decoded")
    def test_read_only(self):
        self.assertFalse(q.decode({"rows":[]})["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
