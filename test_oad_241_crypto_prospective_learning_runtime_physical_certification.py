import ast,subprocess,sys,unittest
from pathlib import Path
ROOT=Path.cwd(); LAUNCHER=ROOT/"run_oracle_LIVE.py"; RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"
def children():
    tree=ast.parse(LAUNCHER.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            return {str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant)}
    raise RuntimeError("CHILDREN missing")
class T(unittest.TestCase):
    def test_physical(self):
        c=children(); print("[PHYSICAL] crypto_learning_runner=",c.get("crypto_learning")); self.assertEqual(c.get("crypto_learning"),RUNNER.name)
        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30); print(p.stdout,end=""); self.assertEqual(p.returncode,0)
        for x in ("prospective_learning=TRUE","probability_enabled=FALSE","direction_enabled=FALSE","publication_allowed=FALSE","execution_authority=FALSE"): self.assertIn(x,p.stdout)
        q=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30); print(q.stdout,end=""); self.assertEqual(q.returncode,0)
        self.assertNotIn("execution_authority=TRUE",LAUNCHER.read_text(encoding="utf-8")); self.assertNotIn("execution_authority=TRUE",RUNNER.read_text(encoding="utf-8"))
        print("[PHYSICAL] supervised_by_orh=True prospective_learning=True terminal_dependency=NONE execution_authority=False")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-241 prospective learning Oracle Live Runtime boundary physically certified")
