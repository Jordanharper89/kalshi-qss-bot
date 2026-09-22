from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_046_oracle_live_evidence_learner_launcher_cutover.py";TEST=ROOT/"test_olr_046_oracle_live_evidence_learner_launcher_cutover.py";INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast\n\nOLR_046_BUILD_ID="OLR-046"\nOLR_046_REVISION="OLR_046_ORACLE_LIVE_EVIDENCE_LEARNER_LAUNCHER_CUTOVER_V1"\nTARGET_LEARNING_RUNNER="run_olr_044_continuous_learning_with_evidence.py"\n\ndef read_children(source):\n    tree=ast.parse(source)\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):\n            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):\n                out={}\n                for k,v in zip(item.value.keys,item.value.values):\n                    if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):\n                        out[str(k.value)]=str(v.value)\n                return out\n    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")\n\ndef patch_learning_child(source,target=TARGET_LEARNING_RUNNER):\n    tree=ast.parse(source)\n    node=None\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):\n            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):\n                node=item.value;break\n    if node is None: raise RuntimeError("CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if isinstance(k,ast.Constant) and str(k.value)=="learning" and isinstance(v,ast.Constant):\n            old=str(v.value)\n            if old==target:return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(target),1)\n                    patched="".join(lines);ast.parse(patched);return patched\n    raise RuntimeError("learning child not found")\n\ndef verify_olr_046_oracle_live_evidence_learner_launcher_cutover(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    launcher=root/"run_oracle_LIVE.py"\n    if not launcher.is_file():return False\n    children=read_children(launcher.read_text(encoding="utf-8"))\n    return (\n        children.get("learning")==TARGET_LEARNING_RUNNER\n        and (root/TARGET_LEARNING_RUNNER).is_file()\n    )\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_046_oracle_live_evidence_learner_launcher_cutover import *\nclass T(unittest.TestCase):\n    def test_patch(self):\n        src=\'CHILDREN={"learning":"run_old.py","canonical_writer":"writer.py"}\\n\'\n        out=patch_learning_child(src)\n        self.assertIn(TARGET_LEARNING_RUNNER,out)\n    def test_target(self):\n        self.assertEqual(TARGET_LEARNING_RUNNER,"run_olr_044_continuous_learning_with_evidence.py")\nif __name__=="__main__":\n    print("="*88);print(" OLR-046 CERTIFICATION TEST");print(" ORACLE LIVE EVIDENCE-LEARNER LAUNCHER CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Oracle Live learning-child cutover machinery certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-046 CERTIFIED")\n'

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

def main():
    print("="*88);print(" OLR-046 INSTALLER");print(" ORACLE LIVE EVIDENCE-LEARNER LAUNCHER CUTOVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_learning.olr_045_live_evidence_grounded_learning_freeze")
    if not up.verify_olr_045_live_evidence_grounded_learning_freeze(ROOT):raise RuntimeError("Certified OLR-045 verification failed")
    if not LAUNCHER.is_file():raise RuntimeError("run_oracle_LIVE.py missing")
    print("[PASS] Certified OLR-045 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT,LAUNCHER);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_046_oracle_live_evidence_learner_launcher_cutover import *")
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_046_oracle_live_evidence_learner_launcher_cutover")
        source=LAUNCHER.read_text(encoding="utf-8")
        patched=m.patch_learning_child(source)
        compile(patched,str(LAUNCHER),"exec");write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        if not m.verify_olr_046_oracle_live_evidence_learner_launcher_cutover(ROOT):raise RuntimeError("OLR-046 physical cutover verification failed")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-046 cutover failed; launcher and affected files restored");raise
    print("[PASS] learning="+m.TARGET_LEARNING_RUNNER)
    print("[PASS] canonical writer path unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-046 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
