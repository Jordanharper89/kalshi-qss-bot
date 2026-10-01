import json,tempfile,unittest,urllib.error
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine as e

class T(unittest.TestCase):
    def setUp(self):
        e._hot_cache={"at":0.0,"rows":[]}

    def test_strategy_registry_and_profitable_regression(self):
        self.assertEqual(set(e.STRATEGIES),{"PUMP_TO_METEORA","METEORA_TO_PUMP"})
        self.assertEqual([x[0] for x in e.GAV_REGRESSION],[0.005,0.01,0.025,0.05])
        self.assertTrue(all(x[1]>0 for x in e.GAV_REGRESSION))
        self.assertLess(max(x[2] for x in e.GAV_REGRESSION)-min(x[2] for x in e.GAV_REGRESSION),4)
        print("[PASS] frozen Gav profitable curve + both proven two-leg directions")

    def test_hotset_uses_confirmed_commitment(self):
        calls=[]
        old=e._rpc
        def fake(method,params):
            calls.append((method,params))
            if method=="getSignaturesForAddress":
                return [{"signature":"S","err":None}]
            if method=="getTransaction":
                return {"blockTime":0,"meta":{"preTokenBalances":[{"mint":"T"}],"postTokenBalances":[]}}
        e._rpc=fake
        try:e.mriya_hot_tokens()
        finally:e._rpc=old
        sig=[x for x in calls if x[0]=="getSignaturesForAddress"][0]
        tx=[x for x in calls if x[0]=="getTransaction"][0]
        self.assertEqual(sig[1][1]["commitment"],"confirmed")
        self.assertEqual(tx[1][1]["commitment"],"confirmed")
        print("[PASS] Mriya hotset fixes prior processed-commitment failure")

    def test_one_hydration_many_sizes(self):
        old_build,old_quote=e.c.build_token_snapshot,e.c.sized_snapshot_opportunities
        n={"build":0,"quote":0}
        e.c.build_token_snapshot=lambda t,p:(n.__setitem__("build",n["build"]+1) or {"token":t})
        def q(s,size):
            n["quote"]+=1
            start=int(size*1e9)
            return [{"token":"T","pump_pool":"P","meteora":{"address":"M"},"start":start,
                     "size_sol":size,"direction":"PUMP_TO_METEORA",
                     "local_net":int(start*.01),"local_bps":100.0}]
        e.c.sized_snapshot_opportunities=q
        try:
            _,rows=e.hydrate_and_rank("T","P",5000)
        finally:
            e.c.build_token_snapshot, e.c.sized_snapshot_opportunities=old_build,old_quote
        self.assertEqual(n["build"],1)
        self.assertGreater(n["quote"],len(e.COARSE_SIZES))
        self.assertTrue(rows)
        print("[PASS] one state hydration supports coarse+fine local size optimization")

    def test_top_only_revalidation_requires_two_slots_and_positive(self):
        old_slot,old_build,old_quote=e._slot,e.c.build_token_snapshot,e.quote_snapshot
        slots=iter([100,102])
        e._slot=lambda:next(slots)
        e.c.build_token_snapshot=lambda t,p:{"token":t}
        e.quote_snapshot=lambda s,z,l:[{"token":"T","pump_pool":"P","meteora":{"address":"M"},
            "start":50_000_000,"size_sol":0.05,"direction":"PUMP_TO_METEORA",
            "net_after_cost_lamports":2_000_000,"net_after_cost_sol":.002,
            "net_after_cost_bps":400.0}]
        try:
            r,d=e.revalidate("T","P",{"size_sol":.05,"direction":"PUMP_TO_METEORA"},5000)
        finally:
            e._slot,e.c.build_token_snapshot,e.quote_snapshot=old_slot,old_build,old_quote
        self.assertTrue(r["qualified"]);self.assertEqual(r["slot_spread"],2)
        print("[PASS] candidate must remain positive in <=2-slot fresh revalidation")

    def test_429_is_contained_not_fatal(self):
        old_u,old_cost,old_exact,old_h=e.candidate_universe,e.landing_cost_lamports,e.exact_pool_ok,e.hydrate_and_rank
        e.candidate_universe=lambda root:[{"token":"T","pump_pool":"P","source":"LIVE_TAPE","age":None}]
        e.landing_cost_lamports=lambda:5000
        e.exact_pool_ok=lambda t,p:(True,"OK")
        def boom(t,p,l):
            raise urllib.error.HTTPError("u",429,"rate",{},None)
        e.hydrate_and_rank=boom
        try:
            with tempfile.TemporaryDirectory() as td:
                s=e.scan_once(td)
                self.assertEqual(s["errors"].get("HTTP_429"),1)
                self.assertIsNone(s["qualified"])
        finally:
            e.candidate_universe,e.landing_cost_lamports,e.exact_pool_ok,e.hydrate_and_rank=old_u,old_cost,old_exact,old_h
        print("[PASS] provider 429 skips candidate without killing scanner")

    def test_no_failed_hot_path_dependencies(self):
        src=Path(e.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("npm install",src)
        self.assertNotIn("subprocess",src)
        self.assertNotIn("getprogramaccounts",src)
        print("[PASS] no Jupiter, Node/npm, subprocess, or per-size program-account fanout in clean bot")

if __name__=="__main__":
    unittest.main(verbosity=2)
