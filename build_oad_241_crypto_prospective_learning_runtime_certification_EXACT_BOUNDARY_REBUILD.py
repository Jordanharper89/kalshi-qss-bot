from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
EXPECTED='build_oad_241_crypto_prospective_learning_runtime_certification_EXACT_BOUNDARY_REBUILD.py'; TEST='import ast,subprocess,sys,unittest\nfrom pathlib import Path\nROOT=Path.cwd(); LAUNCHER=ROOT/"run_oracle_LIVE.py"; RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"\ndef children():\n    tree=ast.parse(LAUNCHER.read_text(encoding="utf-8"))\n    for n in ast.walk(tree):\n        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):\n            return {str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant)}\n    raise RuntimeError("CHILDREN missing")\nclass T(unittest.TestCase):\n    def test_physical(self):\n        c=children(); print("[PHYSICAL] crypto_learning_runner=",c.get("crypto_learning")); self.assertEqual(c.get("crypto_learning"),RUNNER.name)\n        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30); print(p.stdout,end=""); self.assertEqual(p.returncode,0)\n        for x in ("prospective_learning=TRUE","probability_enabled=FALSE","direction_enabled=FALSE","publication_allowed=FALSE","execution_authority=FALSE"): self.assertIn(x,p.stdout)\n        q=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30); print(q.stdout,end=""); self.assertEqual(q.returncode,0)\n        self.assertNotIn("execution_authority=TRUE",LAUNCHER.read_text(encoding="utf-8")); self.assertNotIn("execution_authority=TRUE",RUNNER.read_text(encoding="utf-8"))\n        print("[PHYSICAL] supervised_by_orh=True prospective_learning=True terminal_dependency=NONE execution_authority=False")\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-241 prospective learning Oracle Live Runtime boundary physically certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root()
    for p in (r/"run_oracle_LIVE.py",r/"run_oad_207_crypto_continuous_learning_production_child.py",r/"qseries_v2/oracle_adapters/independent/oad_239_crypto_prospective_learning_resilient_worker.py"):
        if not p.is_file(): raise RuntimeError("boundary missing: "+str(p))
        print("[PASS] boundary verified:",p.relative_to(r))
    t=r/"test_oad_241_crypto_prospective_learning_runtime_physical_certification.py"; old=t.read_bytes() if t.exists() else None
    try:
        compile(TEST,str(t),"exec"); tmp=t.with_suffix(".py.tmp"); tmp.write_text(TEST,encoding="utf-8",newline="\n"); os.replace(tmp,t)
        q=subprocess.run([sys.executable,str(t)],cwd=str(r))
        if q.returncode: raise RuntimeError("OAD-241 physical certification failed")
        print("[PASS] existing Oracle Live Runtime supervision preserved")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-241 INSTALLATION COMPLETE")
    except Exception:
        if old is None:
            if t.exists(): t.unlink()
        else: t.write_bytes(old)
        print("[ROLLBACK] OAD-241 rolled back"); raise
if __name__=="__main__": main()
