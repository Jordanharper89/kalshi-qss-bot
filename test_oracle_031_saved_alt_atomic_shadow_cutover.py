import inspect, unittest
from unittest.mock import patch
from qseries_v2.oracle_execution import oracle_031_saved_alt_atomic_shadow_cutover as q31

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q31.EXECUTION_AUTHORITY)
        self.assertTrue(q31.PAPER_ONLY)
        self.assertFalse(q31.REAL_MONEY_MOVED)

    def test_hot_path_has_no_mriya_lookup(self):
        src=inspect.getsource(q31.saved_alt_attempt_candidate_simulations)
        self.assertNotIn("recent_mriya_alt_keys",src)
        self.assertNotIn("compile_signed",src)

    def test_route_adapter(self):
        r=q31.execution_route({
            "token":"T",
            "start_lamports":1000,
            "pre_sim_net_lamports":20,
            "pre_sim_bps":200.0,
            "alts":["A"],
            "candidates":[("FULL",[])],
        })
        self.assertEqual(r["token"],"T")
        self.assertEqual(r["base_alts"],["A"])
        self.assertEqual(r["original_candidates"],[("FULL",[])])

    def test_saved_alt_return_or_mutation_supported(self):
        route={"token":"T","base_alts":["A"],"original_candidates":[],"start_lamports":1}
        def mutate(root,r):
            r["base_alts"].append("B")
            return None
        with patch.object(q31.q97,"_apply_saved_alt",mutate):
            out,before,after=q31.apply_saved_alt(".",route)
        self.assertEqual(before,["A"])
        self.assertEqual(after,["A","B"])
        self.assertEqual(out["base_alts"],["A","B"])

    def test_helper_stripped_shell_rejected(self):
        route={
            "token":"T","start_lamports":1000,
            "pre_sim_net_lamports":10,"pre_sim_bps":100.0,
            "alts":[],"candidates":[("PUMP_METEORA_ONLY",[])],
        }
        with patch.object(q31.q97,"_apply_saved_alt",lambda root,r:r), \
             patch.object(q31.q87,"repaired_candidates",lambda r:[
                 {"name":"PUMP_METEORA_ONLY","instructions":[],"pump_optional_removed":0}
             ]):
            winner,rows=q31.saved_alt_attempt_candidate_simulations("U",None,route,"BH")
        self.assertIsNone(winner)
        self.assertEqual(rows[0]["error"],"LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL")

    def test_no_broadcast(self):
        src=inspect.getsource(q31)
        self.assertNotIn("sendTransaction(",src)

if __name__=="__main__":
    unittest.main(verbosity=2)
