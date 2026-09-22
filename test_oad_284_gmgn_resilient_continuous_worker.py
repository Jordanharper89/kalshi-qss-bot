import subprocess,sys,unittest
from pathlib import Path

ROOT=Path.cwd(); RUNNER=ROOT/"run_oad_284_gmgn_continuous_intelligence_production_child.py"
class T(unittest.TestCase):
    def test_check(self):
        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(p.stdout,end=""); self.assertEqual(p.returncode,0)
        self.assertIn("[READY] gmgn_intelligence child",p.stdout)
        self.assertIn("execution_authority=FALSE",p.stdout)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-284 resilient GMGN production child boundary certified")
