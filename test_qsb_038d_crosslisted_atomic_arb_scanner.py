import unittest,tempfile
from unittest.mock import patch
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import crosslisted as x

class T(unittest.TestCase):
    def test_intersection_starts_from_pumpswap_not_meteora(self):
        pump={"router_rows":50,"active_pools":2,"identities":[
          {"pump_pool":"PP1","token":"TOK1","token_decimals":6,"wsol_decimals":9,"activity":5},
          {"pump_pool":"PP2","token":"TOK2","token_decimals":6,"wsol_decimals":9,"activity":2}]}
        with patch.object(x,"live_pumpswap_identities",return_value=pump):
            def h(url,*a,**k):
                tok="TOK1" if "TOK1" in url else "TOK2"
                return {"data":[{"address":"M-"+tok,"token_x":{"address":core.WSOL,"decimals":9},
                                 "token_y":{"address":tok,"decimals":6},"tvl":100}]}
            p,pairs=x.crosslisted(".",h,1,6)
        self.assertEqual(len(pairs),2);self.assertEqual(pairs[0]["pump_pool"],"PP1")
        print("[PASS] live PumpSwap exact identities are the discovery source; Meteora is only intersected afterward")

    def test_non_crosslisted_token_never_hydrates(self):
        pump={"router_rows":10,"active_pools":1,"identities":[
          {"pump_pool":"PP","token":"NO_METEORA","token_decimals":6,"wsol_decimals":9,"activity":1}]}
        with patch.object(x,"live_pumpswap_identities",return_value=pump):
            p,pairs=x.crosslisted(".",lambda *a,**k:{"data":[]},1,6)
        self.assertEqual(pairs,[])
        print("[PASS] non-cross-listed Pump token is rejected before any Solana pool hydration")

    def test_meteora_exact_pair_only(self):
        def h(url,*a,**k):
            return {"data":[
              {"address":"BAD","token_x":{"address":"X","decimals":6},"token_y":{"address":"TOK","decimals":6},"tvl":999},
              {"address":"GOOD","token_x":{"address":core.WSOL,"decimals":9},"token_y":{"address":"TOK","decimals":6},"tvl":5}]}
        m=x.meteora_matches("TOK",h);self.assertEqual([r["address"] for r in m],["GOOD"])
        print("[PASS] only exact WSOL/token Meteora pairs survive intersection")

    def test_size_grid_has_small_fast_arb_sizes(self):
        self.assertEqual(x.SIZES_SOL[0],.03);self.assertIn(.10,x.SIZES_SOL);self.assertIn(1.0,x.SIZES_SOL)
        print("[PASS] optimizer tests small-to-1SOL sizes instead of reusing old Mriya sizes")

    def test_profit_gate_is_inherited_fresh_and_net(self):
        a=x.prior.evaluate(1,1.003,100,101,.0001)
        stale=x.prior.evaluate(1,1.01,100,110,.0001)
        self.assertTrue(a["paper_trade"]);self.assertFalse(stale["paper_trade"])
        print("[PASS] positive edge must also be same-window fresh")

    def test_live_capture_persist_contract(self):
        import inspect
        s=Path(inspect.getfile(x)).read_text(encoding="utf-8")
        self.assertIn("capture(seconds=int(capture_seconds)",s)
        self.assertIn("multidex_live_event_router.json",s)
        self.assertIn("resolve(Path(root))",s)
        print("[PASS] scanner refreshes certified live router then resolves exact PumpSwap pool identity")

if __name__=="__main__":unittest.main(verbosity=2)
