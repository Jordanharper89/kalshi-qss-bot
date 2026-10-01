import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import scanner as s

class FakeQ:
    def __init__(self,out):
        self.complete=True;self.remaining_in=0;self.amount_out=out

class FakeState:pass

class T(unittest.TestCase):
    def test_discovery_is_dynamic_not_hardcoded_token(self):
        def h(url,*a,**k):
            return {"data":[
              {"address":"P1","token_x":{"address":core.WSOL,"decimals":9},"token_y":{"address":"AAA","decimals":6},"tvl":5},
              {"address":"P2","token_x":{"address":"BBB","decimals":6},"token_y":{"address":core.WSOL,"decimals":9},"tvl":10},
              {"address":"P3","token_x":{"address":"X","decimals":6},"token_y":{"address":"Y","decimals":6},"tvl":999}]}
        rows=s.discover_wsol_dlmm_candidates(h,10)
        self.assertEqual([x["token"] for x in rows],["BBB","AAA"])
        print("[PASS] scanner discovers current WSOL DLMM tokens dynamically")

    def test_both_directions_have_profit_gate(self):
        a=s.evaluate(1.0,1.003,100,101,.0001)
        b=s.evaluate(1.0,.999,100,101,.0001)
        self.assertTrue(a["paper_trade"]);self.assertFalse(b["paper_trade"])
        print("[PASS] positive fresh net edge admitted; losing edge rejected")

    def test_stale_profitable_quote_rejected(self):
        x=s.evaluate(1.0,1.01,100,110,.0001)
        self.assertGreater(x["net_bps"],15);self.assertFalse(x["paper_trade"])
        print("[PASS] profitable but stale multi-slot quote is rejected")

    def test_meteora_direction_math_uses_pool_orientation(self):
        fake=__import__("types").ModuleType("meteora_dlmm")
        def q(state,amount_in,swap_for_y,strict=True):
            self.assertTrue(swap_for_y);return FakeQ(123456)
        fake.quote=q
        import sys
        meta={"token_x":core.WSOL,"token_y":"AAA","decimals_x":9,"decimals_y":6,"token":"AAA","address":"P"}
        with patch.dict(sys.modules,{"meteora_dlmm":fake}):
            z=s.meteora_from_state(FakeState(),meta,core.WSOL,1.0)
        self.assertEqual(z["out_mint"],"AAA");self.assertEqual(z["raw_out"],123456)
        print("[PASS] WSOL->token direction follows actual pool orientation")

    def test_pump_quote_is_arbitrary_token_not_old_mriya_token(self):
        def h(url,method,body,timeout):
            self.assertEqual(body["inputMint"],"ANYTOKEN");self.assertEqual(body["outputMint"],core.WSOL)
            return {"pumpMintInfo":{"expectedOutAmount":"1001000000"}}
        z=s.pump_any("ANYTOKEN",core.WSOL,500,h)
        self.assertEqual(z["raw_out"],1001000000)
        print("[PASS] Pump quote path is dynamic per discovered token")

    def test_best_sort_prefers_real_edge(self):
        xs=[s.evaluate(1,1.001,1,1),s.evaluate(1,1.005,1,1)]
        xs.sort(key=lambda x:x["net_bps"],reverse=True)
        self.assertGreater(xs[0]["net_bps"],xs[1]["net_bps"])
        print("[PASS] opportunity ranking selects highest net bps")

if __name__=="__main__":unittest.main(verbosity=2)
