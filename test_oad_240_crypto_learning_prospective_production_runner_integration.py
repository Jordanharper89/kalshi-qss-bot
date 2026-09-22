import subprocess,sys,unittest
from pathlib import Path
ROOT=Path.cwd(); RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"
class T(unittest.TestCase):
    def test_contract(self):
        src=RUNNER.read_text(encoding="utf-8")
        for x in ("--check","--cadence-seconds","--horizon-seconds","--acquisition-timeout-seconds","--persistence-timeout-seconds","--max-attempts","run_resilient_prospective_learning_worker"):
            self.assertIn(x,src)
        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(p.stdout,end=""); self.assertEqual(p.returncode,0); self.assertIn("prospective_learning=TRUE",p.stdout); self.assertIn("execution_authority=FALSE",p.stdout)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-240 exact production child interface preserved")
