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

    def function(self,name):
        rows=[n for n in self.tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
        self.assertEqual(len(rows),1,name)
        return rows[0]

    def source(self,name):
        return ast.get_source_segment(self.src,self.function(name)) or ""

    def test_exact_best_is_exact_005_only(self):
        fn=self.function("exact_best")
        floats=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant) and isinstance(n.value,float)]
        self.assertEqual(floats.count(0.005),1)
        for forbidden in (0.001,0.01,0.025,0.05,0.1,0.18,0.28,0.5,1.0,1.4):
            self.assertNotIn(forbidden,floats)

    def test_execution_guard_is_5000000_lamports(self):
        s=self.source("_execute_route_once")
        self.assertIn("5_000_000",s)
        self.assertIn("CANARY_005_START_NOT_EXACT",s)
        self.assertIn("CANARY_005_SIZE_NOT_EXACT",s)

    def test_real_message_fee_is_required(self):
        s=self.source("compile_current")
        self.assertIn('"getFeeForMessage"',s)
        self.assertIn('"fee_lamports"',s)

    def test_transaction_is_signed(self):
        s=self.source("compile_current")
        self.assertIn("q87.c.signed_tx",s)
        self.assertIn("CANARY_005_SIGNER_NOT_INITIALIZED",s)

    def test_simulation_verifies_signature(self):
        fn=self.function("simulate_current")
        found=False
        for row in [n for n in ast.walk(fn) if isinstance(n,ast.Dict)]:
            for k,v in zip(row.keys,row.values):
                if isinstance(k,ast.Constant) and k.value=="sigVerify" and isinstance(v,ast.Constant) and v.value is True:
                    found=True
        self.assertTrue(found)

    def test_after_fee_nonpositive_never_simulates(self):
        s=self.source("_execute_route_once")
        self.assertLess(s.index("if after_fee_net<=0"),s.index("sim=simulate_current"))
        self.assertIn("AFTER_FEE_NONPOSITIVE",s)

    def test_wallet_key_is_loaded_not_printed_or_stored(self):
        self.assertIn('globals()["SIGNER"] = _canary_signer',self.src)
        self.assertNotIn('print(os.getenv("QSB_SOLANA_PRIVATE_KEY"',self.src)
        self.assertNotIn('write_text(os.getenv("QSB_SOLANA_PRIVATE_KEY"',self.src)

    def test_broadcast_still_disabled_for_this_proof(self):
        self.assertIn('"[BROADCAST] disabled"',self.src)
        self.assertNotIn("q87.c.send(",self.src)

if __name__=="__main__":
    unittest.main(verbosity=2)
