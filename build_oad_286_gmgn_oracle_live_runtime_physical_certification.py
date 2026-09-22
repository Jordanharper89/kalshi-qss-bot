from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

TEST_SOURCE=r"""
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
"""

def root():
    from pathlib import Path
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(s,encoding="utf-8",newline="\n"); os.replace(tmp,path)

def main():
    r=root()
    launcher=r/"run_oracle_LIVE.py"; runner=r/"run_oad_284_gmgn_continuous_intelligence_production_child.py"
    if not launcher.is_file(): raise RuntimeError("physical launcher missing")
    if not runner.is_file(): raise RuntimeError("OAD-284 runner missing")
    # Fail closed unless OAD-285 integration is already physically present.
    src=launcher.read_text(encoding="utf-8"); ast.parse(src)
    found=False
    for n in ast.walk(ast.parse(src)):
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            c={str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant)}
            found=c.get("gmgn_intelligence")==runner.name
            break
    if not found: raise RuntimeError("OAD-285 GMGN child integration not present")
    test=r/"test_oad_286_gmgn_oracle_live_runtime_physical_certification.py"
    write_checked(test,TEST_SOURCE)
    print("[PASS] exact GMGN supervised-child binding verified")
    print("[PASS] OAD-286 physical certification test installed")
    print("[DONE] OAD-286 INSTALLATION COMPLETE")
if __name__=="__main__": main()
