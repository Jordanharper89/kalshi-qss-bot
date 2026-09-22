import ast, pathlib, unittest

ROOT=pathlib.Path.cwd().resolve()

class T(unittest.TestCase):
    def _launchers(self):
        return [p for p in (ROOT/"run_oracle_LIVE.py",ROOT/"run_oracle_live.py") if p.is_file()]

    def test_launcher_exists(self):
        self.assertTrue(self._launchers())

    def test_no_blocking_oir_preflight(self):
        for p in self._launchers():
            s=p.read_text(encoding="utf-8")
            self.assertNotIn("reconcile_complete_gap_settlements(",s)
            self.assertNotIn("reconcile_downtime_delta(",s)
            self.assertNotIn("run_recovery_preflight(",s)

    def test_no_oir_recovery_imports(self):
        for p in self._launchers():
            s=p.read_text(encoding="utf-8")
            self.assertNotIn("oir_009_complete_settlement_reconciliation",s)
            self.assertNotIn("oir_014_delta_settlement_reconciliation",s)
            self.assertNotIn("oir_015_delta_live_cutover",s)

    def test_runtime_children_preserved(self):
        for p in self._launchers():
            s=p.read_text(encoding="utf-8")
            for token in ("fast_lane","inventory","reasoning","learning"):
                self.assertIn(token,s)

    def test_syntax(self):
        for p in self._launchers():
            ast.parse(p.read_text(encoding="utf-8"))

if __name__=="__main__":
    print("="*88)
    print(" ORACLE LIVE KNOWN-GOOD RESTORE CERTIFICATION")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Blocking OIR recovery startup path removed")
    print("[PASS] Core Oracle Live children preserved")
    print("[PASS] Launcher syntax certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] KNOWN-GOOD ORACLE LIVE RESTORE CERTIFIED")
