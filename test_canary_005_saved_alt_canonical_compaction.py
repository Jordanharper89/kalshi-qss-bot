from __future__ import annotations
import ast
from pathlib import Path
import unittest

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=TARGET.read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.src)

    def fn(self,name):
        rows=[n for n in self.tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
        self.assertEqual(len(rows),1,name)
        return rows[0]

    def srcfn(self,name):
        return ast.get_source_segment(self.src,self.fn(name)) or ""

    def test_canary_size_preserved(self):
        s=self.srcfn("exact_best")
        self.assertIn("0.005",s)
        for bad in ("0.001","0.010","0.025","0.050","0.100","0.180","0.280","0.500","1.000","1.400"):
            self.assertNotIn(bad,s)

    def test_saved_alt_preload_exists(self):
        s=self.srcfn("preload_canary_saved_alts")
        self.assertIn("_load_alt_state",s)
        self.assertIn("alt_accounts",s)
        self.assertIn("PRELOADED_ALTS",s)
        self.assertIn("PRELOADED_ALT_TABLES",s)

    def test_hot_compile_uses_preloaded_alt_first(self):
        s=self.srcfn("compile_current")
        self.assertIn("PRELOADED_ALTS",s)
        self.assertIn("CANARY_005_COMPILE_ATTEMPT",s)
        self.assertNotIn("_saved_alt(",s)
        self.assertNotIn("_apply_saved_alt(",s)

    def test_no_hot_alt_rpc(self):
        s=self.srcfn("_canonical_cached_alt_accounts")
        self.assertNotIn("rpc(",s)
        self.assertIn("CANARY_005_ALT_NOT_PRELOADED",s)

    def test_preload_happens_before_blockhash(self):
        run=self.srcfn("run")
        self.assertLess(run.index("preload_canary_saved_alts"),run.index("BLOCKHASH.start"))

    def test_shell_remains_rejected(self):
        s=self.srcfn("compile_current")
        self.assertIn("PUMP_METEORA_ONLY",s)
        self.assertIn("LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",s)

    def test_signed_fee_sim_contract_preserved(self):
        c=self.srcfn("compile_current")
        sim=self.srcfn("simulate_current")
        self.assertIn('"getFeeForMessage"',c)
        self.assertIn("q87.c.signed_tx",c)
        self.assertIn('"sigVerify":True',sim.replace(" ","").replace("\n",""))

    def test_broadcast_still_disabled(self):
        self.assertIn('"[BROADCAST] disabled"',self.src)
        self.assertNotIn("q87.c.send(",self.src)

if __name__=="__main__":
    unittest.main(verbosity=2)
