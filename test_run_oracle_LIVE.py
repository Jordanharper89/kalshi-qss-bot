import subprocess,sys,unittest
from pathlib import Path
import run_oracle_LIVE as live
class T(unittest.TestCase):
    def test_boot(self):self.assertTrue(live.build_boot_report().certified)
    def test_check(self):
        p=subprocess.run([sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],capture_output=True,text=True)
        if p.returncode!=0:print(p.stdout);print(p.stderr)
        self.assertEqual(p.returncode,0)
        self.assertIn("continuous reasoning + learning verified",p.stdout)
if __name__=="__main__":
    print("="*72);print(" ORACLE LIVE + OLR-005 LEARNING LAUNCHER TEST");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Oracle launcher bound to supervised continuous learning child")
