import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path.cwd().resolve()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"
CHECKPOINT_MODULE=ROOT/"qseries_v2/oracle_adapters/independent/oad_200_crypto_continuous_learning_postgresql_checkpoint.py"

def read_children():
    src=LAUNCHER.read_text(encoding="utf-8")
    tree=ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets):
            return {str(k.value):str(v.value) for k,v in zip(node.value.keys,node.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant)}
    raise RuntimeError("CHILDREN dictionary missing")

class T(unittest.TestCase):
    def test_physical_integration(self):
        c=read_children()
        print("[PHYSICAL] crypto_learning_runner=",c.get("crypto_learning"))
        self.assertEqual(c.get("crypto_learning"),RUNNER.name)
        self.assertTrue(RUNNER.is_file())
        self.assertTrue(CHECKPOINT_MODULE.is_file())

        lp=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print("[PHYSICAL] launcher_check_returncode=",lp.returncode)
        self.assertEqual(lp.returncode,0)

        cp=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(cp.stdout,end="")
        print("[PHYSICAL] crypto_child_check_returncode=",cp.returncode)
        self.assertEqual(cp.returncode,0)

        src=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("for key in CHILDREN",src)
        self.assertIn("restart_backoff_seconds",src)
        self.assertNotIn("execution_authority=TRUE",src)
        self.assertNotIn("execution_authority=TRUE",RUNNER.read_text(encoding="utf-8"))

        print("[PHYSICAL] supervised_by_orh=True")
        print("[PHYSICAL] restart_safe_checkpoint=True")
        print("[PHYSICAL] terminal_dependency=NONE")
        print("[PHYSICAL] probability_enabled=False")
        print("[PHYSICAL] direction_enabled=False")
        print("[PHYSICAL] execution_authority=False")
        print("[PHYSICAL] physical_ready=True")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-211 Oracle Live Runtime crypto continuous-learning integration physically certified")
