import subprocess,sys,unittest
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_276_solana_continuous_observation_production_runner import evaluate_solana_continuous_runner

ROOT=Path.cwd()
RUNNER=ROOT/"run_oad_276_solana_continuous_observation_production_child.py"

class T(unittest.TestCase):
    def test_check(self):
        r=evaluate_solana_continuous_runner(ROOT)
        print("[ADMISSION]",r)
        self.assertTrue(r.admitted)
        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(p.stdout,end="")
        self.assertEqual(p.returncode,0)
        self.assertIn("tick_seconds=1.0",p.stdout)
        self.assertIn("acquisition_seconds=5.0",p.stdout)
        self.assertIn("pinned_session=TRUE",p.stdout)
        self.assertIn("holder_concentration=DEFERRED",p.stdout)
        self.assertIn("execution_authority=FALSE",p.stdout)

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-276 production Solana continuous-observation child contract certified")
