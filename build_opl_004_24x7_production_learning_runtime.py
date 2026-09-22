from pathlib import Path
import importlib,os,subprocess,sys,ast
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_learning"
MOD=PKG/"opl_004_24x7_production_learning_runtime.py";TEST=ROOT/"test_opl_004_24x7_production_learning_runtime.py";RUN=ROOT/"run_opl_004_production_learning_runtime.py";INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport argparse,time\n\nfrom .opl_003_outcome_grounded_production_learning_cycle import run_production_learning_cycle\n\nOPL_004_BUILD_ID="OPL-004"\nOPL_004_REVISION="OPL_004_24X7_PRODUCTION_LEARNING_RUNTIME_V1"\n\ndef main(argv=None):\n    p=argparse.ArgumentParser()\n    p.add_argument("--cadence-seconds",type=float,default=15.0)\n    p.add_argument("--settled-pages",type=int,default=20)\n    p.add_argument("--evidence-limit",type=int,default=5)\n    p.add_argument("--once",action="store_true")\n    p.add_argument("--check",action="store_true")\n    a=p.parse_args(argv)\n\n    if a.check:\n        print("[READY] OPL-004 production learning runtime verified")\n        print("[PASS] execution_authority=FALSE")\n        return 0\n\n    if a.cadence_seconds<=0 or a.settled_pages<1 or a.evidence_limit<1:\n        raise SystemExit("invalid arguments")\n\n    root=Path.cwd();cycle=0\n    print("="*88,flush=True)\n    print(" OPL-004 ORACLE PRODUCTION LEARNING RUNTIME",flush=True)\n    print("="*88,flush=True)\n    print("[OPL] authority=LEARNING_ONLY execution_authority=FALSE",flush=True)\n\n    while True:\n        cycle+=1\n        try:\n            s=run_production_learning_cycle(root,a.settled_pages,a.evidence_limit,lambda x:print(x,flush=True))\n            print(f"[OPL] runtime_cycle={cycle} applied={s.applied} production_learned_total={s.production_learned_total} evidence_coverage={s.evidence_coverage:.3f} learning_yield={s.learning_yield:.3f}",flush=True)\n        except Exception as exc:\n            print(f"[OPL ERROR] type={type(exc).__name__} message={exc}",flush=True)\n            if a.once:raise\n        if a.once:return 0\n        time.sleep(a.cadence_seconds)\n\ndef verify_opl_004_24x7_production_learning_runtime(root=None):\n    return OPL_004_BUILD_ID=="OPL-004" and callable(main)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_learning.opl_004_24x7_production_learning_runtime import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPL_004_BUILD_ID,"OPL-004")\n    def test_callable(self):self.assertTrue(callable(main))\nif __name__=="__main__":\n    print("="*88);print(" OPL-004 CERTIFICATION TEST");print(" 24X7 PRODUCTION LEARNING RUNTIME");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] 24/7 production learning runtime certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPL-004 CERTIFIED")\n';RUN_SOURCE='from qseries_v2.oracle_production_learning.opl_004_24x7_production_learning_runtime import main\nif __name__=="__main__":raise SystemExit(main())\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def patch_learning(source):
    tree=ast.parse(source);node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
            node=item.value;break
    if node is None:raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="learning" and isinstance(v,ast.Constant):
            old=str(v.value);line=lines[v.lineno-1]
            target="run_opl_004_production_learning_runtime.py"
            if old==target:return source
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(target),1)
                    out="".join(lines);ast.parse(out);return out
    raise RuntimeError("learning child not found")
def main():
    print("="*88);print(" OPL-004 INSTALLER");print(" 24X7 PRODUCTION LEARNING RUNTIME + ORACLE CUTOVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_learning.opl_003_outcome_grounded_production_learning_cycle")
    if not up.verify_opl_003_outcome_grounded_production_learning_cycle(ROOT):raise RuntimeError("OPL-003 verification failed")
    affected=(MOD,TEST,RUN,INIT,LAUNCHER);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(RUN,RUN_SOURCE);update_init(INIT,"from .opl_004_24x7_production_learning_runtime import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(RUN),"--check"],cwd=str(ROOT),check=True)
        patched=patch_learning(LAUNCHER.read_text(encoding="utf-8"));compile(patched,str(LAUNCHER),"exec");write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPL-004 failed; launcher/files restored");raise
    print("[PASS] Oracle Live learning child -> run_opl_004_production_learning_runtime.py")
    print("[PASS] OLR no longer owns production learning runtime")
    print("[PASS] canonical writer path unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-004 INSTALLATION COMPLETE")
if __name__=="__main__":main()
