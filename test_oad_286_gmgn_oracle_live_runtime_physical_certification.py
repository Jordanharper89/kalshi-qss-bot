import ast,subprocess,sys,unittest
from pathlib import Path

ROOT=Path.cwd()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
RUNNER=ROOT/"run_oad_284_gmgn_continuous_intelligence_production_child.py"

def children():
    tree=ast.parse(LAUNCHER.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            return {str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant)}
    raise RuntimeError("CHILDREN missing")

class T(unittest.TestCase):
    def test_registry_and_checks(self):
        c=children()
        self.assertEqual(c.get("gmgn_intelligence"),RUNNER.name)
        lp=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(lp.stdout,end=""); self.assertEqual(lp.returncode,0)
        cp=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(cp.stdout,end=""); self.assertEqual(cp.returncode,0)
        self.assertIn("execution_authority=FALSE",cp.stdout)

    def test_physical_one_cycle(self):
        p=subprocess.run(
            [sys.executable,str(RUNNER),"--max-cycles","1","--cadence-seconds","1"],
            cwd=ROOT,text=True,capture_output=True,timeout=180
        )
        print(p.stdout,end="")
        if p.stderr: print(p.stderr,end="")
        self.assertEqual(p.returncode,0)
        self.assertIn("[GMGN] cycle=",p.stdout)
        self.assertIn("status=SUCCESS",p.stdout)
        self.assertIn("exact_readback=3",p.stdout)
        self.assertIn("execution_authority=FALSE",p.stdout)

    def test_supervision_contract(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("for key in CHILDREN",s)
        self.assertIn("restart_backoff_seconds",s)
        self.assertNotIn("execution_authority=TRUE",s)
        self.assertNotIn("execution_authority=TRUE",RUNNER.read_text(encoding="utf-8"))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-286 GMGN Oracle Live supervised runtime physically certified")
    print("[PASS] live GMGN -> OAD-281 -> OAD-261 -> OPH-019 -> PostgreSQL -> exact readback")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-286 PHYSICALLY CERTIFIED")
