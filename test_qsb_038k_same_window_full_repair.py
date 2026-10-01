import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import exactpool as e

PAIR={"token":"T","pump_pool":"P","meteora":{"address":"M","token_x":"So11111111111111111111111111111111111111112","token_y":"T","decimals_x":9,"decimals_y":6}}

class T(unittest.TestCase):
    def test_raw_profit_must_be_revalidated(self):
        rows=[
          {"direction":"PUMP_TO_METEORA","token":"T","pool":"M","pump_pool":"P","start_sol":1.0,
           "end_sol":1.08,"net_sol":.07999,"net_bps":799.9,"slot_spread":1,
           "pre_sim_candidate":True,"pump_transaction_present":True},
        ]
        calls={"n":0}
        def q(root,pair,size,direction,http,rpc):
            calls["n"]+=1
            if calls["n"]<=30:
                return (dict(rows[0]),{"estimated_total_fee_sol":.000005})
            return ({"direction":"PUMP_TO_METEORA","token":"T","pool":"M","pump_pool":"P",
                     "start_sol":1.0,"end_sol":.99,"net_sol":-.010005,"net_bps":-100.05,
                     "slot_spread":1,"pre_sim_candidate":False,"pump_transaction_present":True},
                    {"estimated_total_fee_sol":.000005})
        with patch.object(e,"verify_exact_pump_pool",return_value={"discovered_pool":"P","canonical_pool":"P","verified":True}), \
             patch.object(e,"_quote_once",side_effect=q):
            best,_,_,_,_=e.optimize_pair(".",PAIR,http=lambda *a,**k:{},rpc_fn=lambda *a,**k:None)
        self.assertTrue(best["revalidated"]);self.assertFalse(best["pre_sim_candidate"])
        print("[PASS] raw +799.9 bps edge is rejected when fresh revalidation is negative")

    def test_partial_meteora_quote_hard_rejected(self):
        class X:
            def get(self,k,d=None): return True if k=="partial" else ("T" if k=="out_mint" else 1000 if k=="raw_out" else d)
            def __getitem__(self,k): return self.get(k)
        with patch.object(e.prior,"meteora_from_state",return_value=X()):
            with self.assertRaisesRegex(RuntimeError,"METEORA_PARTIAL_QUOTE"):
                e._dir_meteora_to_pump("rpc","state",PAIR,.1,lambda *a,**k:{},lambda *a,**k:1)
        print("[PASS] partial Meteora quote can never become candidate economics")

    def test_total_window_counts_hydration(self):
        row={"direction":"PUMP_TO_METEORA","token":"T","pool":"M","pump_pool":"P",
             "start_sol":.1,"end_sol":.102,"slot_end":104,"pump_transaction_present":True}
        x=e._finalize(row,{"estimated_total_fee_sol":.000005},100,103)
        self.assertEqual(x["slot_spread"],4);self.assertFalse(x["pre_sim_candidate"])
        print("[PASS] freshness begins before pool-state hydration, not after")

    def test_two_slot_positive_admitted(self):
        row={"direction":"PUMP_TO_METEORA","token":"T","pool":"M","pump_pool":"P",
             "start_sol":.1,"end_sol":.102,"slot_end":102,"pump_transaction_present":True}
        x=e._finalize(row,{"estimated_total_fee_sol":.000005},100,101)
        self.assertTrue(x["pre_sim_candidate"])
        print("[PASS] genuine <=2-slot positive net quote can survive")

if __name__=="__main__":unittest.main(verbosity=2)
