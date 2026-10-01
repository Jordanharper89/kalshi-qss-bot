import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_pretrade_replica.core import *

WSOL="So11111111111111111111111111111111111111112";TOK="T"
def rec(sig,bps,start=1.0,venues=("METEORA_DLMM","PUMP_SWAP"),path=(WSOL,TOK,WSOL)):
    legs=[]
    amt=start
    outs=[100.0,start*(1+bps/10000)]
    for i,v in enumerate(venues):
        legs.append({"resolved":True,"venue":v,"input_asset":path[i],"input_amount":amt,
                     "output_asset":path[i+1],"output_amount":outs[i]})
        amt=outs[i]
    return {"signature":sig,"failed":False,"venue_chain":venues,
            "chain":{"contiguous":True,"closed":True,"gross_bps":bps,"start_amount":start,"legs":legs}}
class T(unittest.TestCase):
    def test_learns_two_win_mriya_family(self):
        r={"records":[rec("A",118.37,1.74628),rec("B",96.31,.699517)]}
        t=learned_templates(r);self.assertEqual(len(t),1);self.assertEqual(t[0]["wins"],2)
        self.assertEqual(t[0]["venues"],("METEORA_DLMM","PUMP_SWAP"))
        print("[PASS] clean repeated Mriya DLMM->PumpSwap family becomes pretrade template")
    def test_absurd_decimal_route_is_rejected(self):
        x=rec("BAD",10045835155465.95)
        self.assertTrue(reject_decimal_anomaly(x))
        r={"records":[rec("A",118.37),rec("B",96.31),x]}
        t=learned_templates(r);self.assertEqual(t[0]["wins"],2)
        print("[PASS] known decimal-unit anomaly cannot train pretrade strategy")
    def test_exact_roundtrip_profit_gate(self):
        qs=[
          {"exact":True,"expected_input_asset":WSOL,"input_asset":WSOL,"input_amount":1.0,"output_amount":100.0},
          {"exact":True,"expected_input_asset":TOK,"input_asset":TOK,"input_amount":100.0,"output_amount":1.0124},
        ]
        x=evaluate_roundtrip(1.0,qs,tx_cost_anchor=.0021,min_net_bps=10)
        self.assertTrue(x["qualified"]);self.assertAlmostEqual(x["net_amount"],.0103,places=9)
        print("[PASS] exact quote chain subtracts transaction cost before paper admission")
    def test_nonexact_quote_fails_closed(self):
        x=evaluate_roundtrip(1.0,[{"exact":False}],0)
        self.assertFalse(x["qualified"]);self.assertEqual(x["reason"],"NON_EXACT_QUOTE")
        print("[PASS] historical/approximate quote can never create paper opportunity")
    def test_asset_chain_mismatch_fails(self):
        qs=[{"exact":True,"expected_input_asset":WSOL,"input_asset":"WRONG","input_amount":1,"output_amount":2}]
        x=evaluate_roundtrip(1,qs);self.assertFalse(x["qualified"])
        print("[PASS] route asset mismatch fails closed")
    def test_small_edge_rejected_after_cost(self):
        qs=[
          {"exact":True,"expected_input_asset":WSOL,"input_asset":WSOL,"input_amount":1,"output_amount":100},
          {"exact":True,"expected_input_asset":TOK,"input_asset":TOK,"input_amount":100,"output_amount":1.001},
        ]
        x=evaluate_roundtrip(1,qs,.001);self.assertFalse(x["qualified"])
        print("[PASS] gross spread is insufficient when net-after-cost edge misses gate")
if __name__=="__main__":unittest.main(verbosity=2)
