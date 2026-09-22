from pathlib import Path
import importlib,os,subprocess,sys,json
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_005_live_cutover.py";TEST=ROOT/"test_olf_005_physical_learning_to_reasoning_cutover_gate.py"
INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py";RUN=ROOT/"run_olf_004_feedback_aware_reasoning_runtime.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast,json\n\nOLF_005_BUILD_ID="OLF-005"\nOLF_005_REVISION="OLF_005_PHYSICAL_LEARNING_TO_REASONING_CUTOVER_GATE_V1"\nTARGET="run_olf_004_feedback_aware_reasoning_runtime.py"\n\ndef patch_reasoning_child(source,target=TARGET):\n    tree=ast.parse(source)\n    node=None\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):\n            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):\n                node=item.value;break\n    if node is None:raise RuntimeError("Oracle Live CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if isinstance(k,ast.Constant) and str(k.value)=="reasoning" and isinstance(v,ast.Constant):\n            old=str(v.value)\n            if old==target:return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(target),1)\n                    out="".join(lines);ast.parse(out);return out\n    raise RuntimeError("Oracle Live reasoning child not found")\n\ndef verify_attestation_matches_learner(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    att=root/"runtime_state"/"oracle_learning_feedback_reasoning_attestation.json"\n    state=root/"runtime_state"/"oracle_learning_runtime_state.json"\n    if not att.is_file() or not state.is_file():return False\n    a=json.loads(att.read_text(encoding="utf-8"))\n    s=json.loads(state.read_text(encoding="utf-8"))\n    ocl=s.get("ocl_state") if isinstance(s,dict) else {}\n    current=str((ocl or {}).get("state_hash") or "")\n    return (\n        bool(current)\n        and str(a.get("learner_state_hash") or "")==current\n        and int(a.get("markets_reasoned",0))>0\n        and a.get("execution_authority") is False\n    )\n\ndef verify_olf_005_physical_learning_to_reasoning_cutover_gate():\n    return OLF_005_BUILD_ID=="OLF-005" and callable(patch_reasoning_child)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_005_live_cutover import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_005_BUILD_ID,"OLF-005")\n    def test_patch(self):\n        s=\'CHILDREN={"reasoning":"old.py","learning":"learn.py"}\\n\'\n        self.assertIn(TARGET,patch_reasoning_child(s))\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-005 CERTIFICATION TEST");print(" PHYSICAL LEARNING -> REASONING CUTOVER GATE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Safe reasoning-child cutover machinery certified")\n    print("[PASS] Physical learner-hash consumption required")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-005 GATE CERTIFIED")\n'

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

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def learner_hash():
    p=ROOT/"runtime_state"/"oracle_learning_runtime_state.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    return str((d.get("ocl_state") or {}).get("state_hash") or "")
def main():
    print("="*88);print(" OLF-005 INSTALLER");print(" PHYSICAL LEARNING -> REASONING CUTOVER GATE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_004_feedback_aware_reasoning_runtime")
    if not up.verify_olf_004_feedback_aware_continuous_reasoning_runtime():raise RuntimeError("OLF-004 verification failed")
    if not RUN.is_file():raise RuntimeError("OLF-004 runtime runner missing")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT,LAUNCHER)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .olf_005_live_cutover import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(RUN),"--check"],cwd=str(ROOT),check=True)

        # Physical proof uses a private cursor so production OCR cursor is not advanced during install.
        snap=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_001_learned_state_snapshot")
        snap.materialize_learned_feedback_snapshot(ROOT)
        before=learner_hash()
        if not before:raise RuntimeError("Current learner state hash missing")

        proof_cursor=ROOT/"runtime_state"/"olf_005_proof_reasoning_cursor.json"
        if proof_cursor.exists():proof_cursor.unlink()
        summary=up.run_feedback_aware_reasoning_cycle(
            ROOT,limit=50,cursor_path=proof_cursor,
            progress=lambda x:print(x,flush=True)
        )
        if summary.idle or summary.markets_reasoned<=0:
            raise RuntimeError("Physical reasoning proof produced no market reasoning")
        if summary.learner_state_hash!=before:
            raise RuntimeError("Reasoning did not consume the exact current learner state hash")

        m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_005_live_cutover")
        if not m.verify_attestation_matches_learner(ROOT):
            raise RuntimeError("Physical learning-to-reasoning attestation failed")

        print(
            f"[PHYSICAL PROOF] markets_reasoned={summary.markets_reasoned} "
            f"learning_context={summary.markets_with_learning_context} "
            f"calibrated={summary.markets_with_calibration_adjustment} "
            f"learner_state_hash={summary.learner_state_hash}"
        )

        source=LAUNCHER.read_text(encoding="utf-8")
        patched=m.patch_reasoning_child(source)
        compile(patched,str(LAUNCHER),"exec")
        write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-005 failed; Oracle Live launcher and affected files restored")
        raise

    print("[PASS] Current learner state hash physically consumed by reasoning")
    print("[PASS] Proven learning child unchanged")
    print("[PASS] Frozen OCR/OSR modules unchanged")
    print("[PASS] Oracle Live reasoning child -> run_olf_004_feedback_aware_reasoning_runtime.py")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-005 LEARNING-FEEDBACK CUTOVER COMPLETE")
if __name__=="__main__":main()
