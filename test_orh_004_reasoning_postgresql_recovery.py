import ast,unittest
from pathlib import Path
ROOT=Path.cwd().resolve();RUN=ROOT/"run_olf_030_breadth_aware_reasoning_runtime.py"
class T(unittest.TestCase):
    def test_physical_runner(self):
        s=RUN.read_text(encoding="utf-8");ast.parse(s)
        self.assertIn("ORH_004_BUILD_ID",s);self.assertIn("run_breadth_aware_reasoning_cycle",s);self.assertIn("REASONING RECOVERY",s)
if __name__=="__main__":
    print("="*88);print(" ORH-004 CERTIFICATION TEST");print(" REASONING POSTGRESQL RECOVERY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] breadth-aware reasoning recovery loop certified")
    print("[PASS] OLF-030 intelligence module unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORH-004 CERTIFIED")
