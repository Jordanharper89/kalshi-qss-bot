import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import exactpool as e

PAIR={"token":"TOK","pump_pool":"POOL123","meteora":{"address":"MET","token_x":core.WSOL,"token_y":"TOK","decimals_x":9,"decimals_y":6}}

class T(unittest.TestCase):
    def test_exact_pool_match_required(self):
        def h(url,*a,**k):return {"complete":True,"pump_swap_pool":"POOL123"}
        x=e.verify_exact_pump_pool(PAIR,h);self.assertTrue(x["verified"])
        print("[PASS] exact discovered Pump pool must match canonical coin-state pool")

    def test_pool_mismatch_rejected(self):
        def h(url,*a,**k):return {"complete":True,"pump_swap_pool":"OTHER"}
        with self.assertRaisesRegex(RuntimeError,"PUMP_POOL_MISMATCH"):e.verify_exact_pump_pool(PAIR,h)
        print("[PASS] generic mint route cannot silently substitute another Pump pool")

    def test_ungraduated_rejected(self):
        def h(url,*a,**k):return {"complete":False,"pump_swap_pool":"POOL123"}
        with self.assertRaisesRegex(RuntimeError,"NOT_GRADUATED"):e.verify_exact_pump_pool(PAIR,h)
        print("[PASS] bonding-curve token cannot masquerade as PumpSwap AMM pair")

    def test_api_quote_keeps_transaction_evidence(self):
        calls=[]
        def h(url,method="GET",body=None,timeout=15):
            calls.append((url,method,body))
            if "coins-v2" in url:return {"complete":True,"pump_swap_pool":"POOL123"}
            return {"transaction":"BASE64TX","pumpMintInfo":{"expectedOutAmount":"123456"}}
        q=e.exact_api_quote(PAIR,"TOK",core.WSOL,999,h)
        self.assertEqual(q["raw_out"],123456);self.assertTrue(q["transaction_present"])
        self.assertEqual(calls[-1][2]["inputMint"],"TOK")
        print("[PASS] exact-bound Pump quote preserves returned transaction for later simulation")

    def test_fee_and_fresh_gate(self):
        r={"start_sol":.03,"end_sol":.03012649,"slot_start":10,"slot_end":11}
        x=e.finalize(r,{"estimated_total_fee_sol":.000005})
        self.assertTrue(x["pre_sim_candidate"]);self.assertGreater(x["net_bps"],15)
        print("[PASS] dynamic fee + <=2-slot positive edge produces pre-sim candidate")

    def test_stale_rejected(self):
        r={"start_sol":.03,"end_sol":.031,"slot_start":10,"slot_end":13}
        x=e.finalize(r,{"estimated_total_fee_sol":.000005})
        self.assertFalse(x["pre_sim_candidate"])
        print("[PASS] stale profitable quote rejected")

if __name__=="__main__":unittest.main(verbosity=2)
