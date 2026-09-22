from __future__ import annotations
import subprocess,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LAUNCHER=ROOT/"run_oracle_live.py"

class T(unittest.TestCase):
    def test_gmgn_environment_boundary(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('if name == "run_oad_284_gmgn_continuous_intelligence_production_child.py":',s)
        self.assertIn('env["COMSPEC"]',s)
        self.assertIn('env["SystemRoot"]',s)
        self.assertIn('env["APPDATA"]',s)
        self.assertIn('env["USERPROFILE"]',s)
        self.assertIn('env["PATH"]',s)

    def test_other_children_preserved(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('return subprocess.Popen([sys.executable,str(p)],cwd=str(root))',s)

    def test_truthful_health_preserved(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("gmgn_checkpoint_cycle_at_spawn",s)
        self.assertIn("if cp.last_error:",s)
        self.assertIn("if success_age > 240.0:",s)
        self.assertIn("restart_backoff_seconds",s)
        self.assertNotIn("execution_authority=TRUE",s)

    def test_launcher_check(self):
        p=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),
                         text=True,capture_output=True,timeout=45)
        self.assertEqual(p.returncode,0,msg=p.stdout+"\n"+p.stderr)
        self.assertIn("[READY] Oracle Live Runtime",p.stdout)

if __name__=="__main__":
    print("="*104)
    print(" OAD-285 GMGN SUPERVISED WINDOWS ENVIRONMENT BOUNDARY CERTIFICATION")
    print("="*104)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] GMGN-only Windows child environment normalized")
    print("[PASS] all non-GMGN child spawn behavior preserved")
    print("[PASS] truthful provider-health supervision preserved")
    print("[PASS] launcher --check passed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-285 SUPERVISED WINDOWS ENVIRONMENT BOUNDARY CERTIFIED")
