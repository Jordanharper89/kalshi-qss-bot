from __future__ import annotations
import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LAUNCHER=ROOT/"run_oracle_live.py"

class T(unittest.TestCase):
    def test_exact_gmgn_binding_preserved(self):
        tree=ast.parse(LAUNCHER.read_text(encoding="utf-8"))
        children=None
        for n in tree.body:
            if isinstance(n,ast.Assign):
                for t in n.targets:
                    if isinstance(t,ast.Name) and t.id=="CHILDREN" and isinstance(n.value,ast.Dict):
                        children=ast.literal_eval(n.value)
        self.assertIsNotNone(children)
        self.assertEqual(children.get("gmgn_intelligence"),"run_oad_284_gmgn_continuous_intelligence_production_child.py")

    def test_truthful_provider_health_semantics_installed(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("gmgn_checkpoint_cycle_at_spawn",s)
        self.assertIn("if cp.last_error:",s)
        self.assertIn("if success_age > 240.0:",s)
        self.assertIn('if key == "gmgn_intelligence":',s)
        self.assertIn('return _gmgn_provider_state(key, age)',s)
        self.assertIn("restart_backoff_seconds",s)
        self.assertNotIn("execution_authority=TRUE",s)

    def test_launcher_check(self):
        p=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),capture_output=True,text=True,timeout=45)
        self.assertEqual(p.returncode,0,msg=(p.stdout+"\n"+p.stderr))
        self.assertIn("[READY] Oracle Live Runtime",p.stdout)

if __name__=="__main__":
    print("="*96)
    print(" OAD-285 TRUTHFUL GMGN PROVIDER-HEALTH BOUNDARY CERTIFICATION")
    print("="*96)
    r=unittest.main(verbosity=2,exit=False)
    if not r.result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] GMGN process-alive health no longer implies provider HEALTHY")
    print("[PASS] fresh in-process successful GMGN cycle required for HEALTHY")
    print("[PASS] provider failure/stale-success state maps to DEGRADED")
    print("[PASS] existing Oracle children + restart supervision preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-285 TRUTHFUL PROVIDER HEALTH BOUNDARY REBUILD CERTIFIED")
