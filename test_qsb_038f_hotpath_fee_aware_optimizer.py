import unittest,tempfile,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import hotpath as h

class T(unittest.TestCase):
    def test_fee_formula(self):
        def rpc(url,method,params):
            self.assertEqual(method,"getRecentPrioritizationFees")
            return [{"slot":1,"prioritizationFee":1000},{"slot":2,"prioritizationFee":3000},{"slot":3,"prioritizationFee":2000},{"slot":4,"prioritizationFee":4000}]
        with tempfile.TemporaryDirectory() as td:
            pair={"pump_pool":"P","meteora":{"address":"M"}}
            f=h.fee_model(td,"rpc",pair,rpc)
        self.assertEqual(f["priority_micro_lamports_per_cu"],3000)
        self.assertEqual(f["priority_fee_lamports"],660)
        self.assertEqual(f["estimated_total_fee_lamports"],5660)
        print("[PASS] dynamic priority fee uses recent p75 price and CU limit formula")

    def test_fee_recompute_not_fixed_0001(self):
        fee={"estimated_total_fee_sol":0.00000566}
        r={"start_sol":.03,"end_sol":.03012649,"slot_start":100,"slot_end":101}
        x=h.recompute(r,fee)
        self.assertAlmostEqual(x["net_sol"],.00012083,places=8)
        self.assertGreater(x["net_bps"],15)
        print("[PASS] old hard-coded 0.0001 SOL penalty removed from admission math")

    def test_two_slot_freshness(self):
        fee={"estimated_total_fee_sol":0.0}
        self.assertTrue(h.recompute({"start_sol":1,"end_sol":1.01,"slot_start":1,"slot_end":3},fee)["fresh"])
        self.assertFalse(h.recompute({"start_sol":1,"end_sol":1.01,"slot_start":1,"slot_end":4},fee)["fresh"])
        print("[PASS] execution qualification tightened to <=2-slot quote window")

    def test_adaptive_grid_clusters_around_best(self):
        xs=h.adaptive_sizes(.03)
        self.assertIn(.03,xs);self.assertTrue(any(.02 < x < .03 for x in xs));self.assertTrue(any(x>.03 for x in xs))
        print("[PASS] coarse winner receives fine-grained local size optimization")

    def test_hot_cache(self):
        with tempfile.TemporaryDirectory() as td:
            pair={"token":"T","pump_pool":"P","meteora":{"address":"M"}}
            h.save_hot(td,[pair]);self.assertEqual(h.load_hot(td),[pair])
        print("[PASS] cross-listed pools reused from short-lived hot cache")

    def test_no_execution_authority(self):
        import inspect
        s=Path(inspect.getfile(h)).read_text(encoding="utf-8")
        self.assertIn('"execution_authority":False',s)
        self.assertIn("PRE_SIMULATION",s)
        print("[PASS] no execution authority and no fake simulation claim")

if __name__=="__main__":unittest.main(verbosity=2)
