import unittest,tempfile,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.core import *

class T(unittest.TestCase):
    def test_clean_sizes(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json";p.parent.mkdir(parents=True)
            def r(sig,s,b):
                return {"signature":sig,"failed":False,"venue_chain":["METEORA_DLMM","PUMP_SWAP"],
                  "chain":{"closed":True,"contiguous":True,"gross_bps":b,"start_amount":s,"legs":[
                    {"input_asset":WSOL,"output_asset":TOKEN},{"output_asset":WSOL}]}}
            p.write_text(json.dumps({"records":[r("a",.7,96),r("b",1.7,118),r("bad",1,999999)]}))
            self.assertEqual(clean_sizes(td),[.7,1.7])
        print("[PASS] only clean repeated Mriya sizes survive")
    def test_pool_discovery_exact_pair(self):
        def h(url,*a,**k):
            return {"data":[
              {"address":"BAD","token_x":{"address":"X","decimals":6},"token_y":{"address":"Y","decimals":9},"tvl":999},
              {"address":"LOW","token_x":{"address":WSOL,"decimals":9},"token_y":{"address":TOKEN,"decimals":6},"tvl":1},
              {"address":"HIGH","token_x":{"address":TOKEN,"decimals":6},"token_y":{"address":WSOL,"decimals":9},"tvl":5}]}
        x=discover_meteora_pool(h);self.assertEqual(x["address"],"HIGH");self.assertEqual(x["decimals_x"],6)
        print("[PASS] Meteora discovery selects exact WSOL/target pair, highest TVL")
    def test_pump_expected_out_strict(self):
        def h(url,method,body,timeout):
            return {"pumpMintInfo":{"hasGraduated":True,"expectedOutAmount":"1012300000"}}
        q=pump_quote(123456,h);self.assertAlmostEqual(q["sol_out"],1.0123,places=9)
        print("[PASS] Pump official API expectedOutAmount becomes exact paper output")
    def test_pump_missing_expected_out_fails(self):
        def h(*a,**k):return {"pumpMintInfo":{"hasGraduated":True}}
        with self.assertRaises(RuntimeError):pump_quote(100,h)
        print("[PASS] missing Pump expectedOutAmount fails closed")
    def test_net_after_cost(self):
        x=pnl(1.0,1.0124,.0021);self.assertAlmostEqual(x["net_sol"],.0103,places=9);self.assertTrue(x["qualified"])
        print("[PASS] pre-trade net subtracts cost before paper admission")
    def test_python_only_source(self):
        import inspect
        import qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.core as c
        s=Path(inspect.getfile(c)).read_text().lower()
        self.assertNotIn('["npm"',s);self.assertNotIn('["node"',s)
        self.assertIn("meteora-dlmm==0.3.0",s)
        print("[PASS] runtime has no Node/npm dependency")
    def test_authority_false(self):
        import qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb as q
        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
        print("[PASS] paper-only; execution authority false")
if __name__=="__main__":unittest.main(verbosity=2)
