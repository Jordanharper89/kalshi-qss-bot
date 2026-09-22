import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path.cwd().resolve()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"

def children():
    source=LAUNCHER.read_text(encoding="utf-8")
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets):
            return {str(k.value):str(v.value) for k,v in zip(node.value.keys,node.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant)}
    raise RuntimeError("CHILDREN missing")

class T(unittest.TestCase):
    def test_registry(self):
        c=children()
        self.assertEqual(c.get("crypto_learning"),RUNNER.name)
    def test_orh_dynamic_supervision(self):
        src=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("for key in CHILDREN",src)
        self.assertIn("states = {key: _child_state(key, now) for key in CHILDREN}",src)
        self.assertIn("restart_counts = {k: 0 for k in CHILDREN}",src)
        self.assertIn("restart_backoff_seconds",src)
    def test_child_check(self):
        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(p.stdout,end="")
        self.assertEqual(p.returncode,0)
        self.assertIn("[READY] crypto_learning child",p.stdout)
        self.assertIn("execution_authority=FALSE",p.stdout)
    def test_launcher_check(self):
        p=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(p.stdout,end="")
        self.assertEqual(p.returncode,0)
    def test_execution_boundary(self):
        self.assertNotIn("execution_authority=TRUE",LAUNCHER.read_text(encoding="utf-8"))
        self.assertNotIn("execution_authority=TRUE",RUNNER.read_text(encoding="utf-8"))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-210 crypto learning child integrated into truthful ORH supervision")
