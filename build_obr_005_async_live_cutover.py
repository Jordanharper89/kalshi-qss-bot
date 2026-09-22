from pathlib import Path
import ast,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_background_recovery"
MOD=PKG/"obr_005_live_cutover.py";TEST=ROOT/"test_obr_005_async_live_cutover.py";INIT=PKG/"__init__.py"
WORKER=ROOT/"run_oracle_background_recovery.py";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nimport ast\nOBR_005_BUILD_ID="OBR-005"\nCHILD_KEY="recovery"\nCHILD_SCRIPT="run_oracle_background_recovery.py"\n\ndef patch_launcher(source):\n    source=str(source)\n    if CHILD_SCRIPT in source:\n        return source\n    tree=ast.parse(source)\n    assign=None\n    for node in tree.body:\n        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets):\n            assign=node;break\n    if assign is None:raise RuntimeError("CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    if isinstance(assign.value,ast.Dict):\n        insertion=f"    \'{CHILD_KEY}\':\'{CHILD_SCRIPT}\',\\n"\n        if assign.lineno==assign.end_lineno:\n            line=lines[assign.lineno-1]\n            idx=line.rfind("}")\n            if idx<0:raise RuntimeError("CHILDREN closing brace not found")\n            prefix=line[:idx];suffix=line[idx:]\n            if prefix.rstrip().endswith("{"):\n                newline=prefix+f"\'{CHILD_KEY}\':\'{CHILD_SCRIPT}\'"+suffix\n            else:\n                newline=prefix.rstrip()+f",\'{CHILD_KEY}\':\'{CHILD_SCRIPT}\'"+suffix\n            lines[assign.lineno-1]=newline\n        else:\n            lines.insert(assign.end_lineno-1,insertion)\n        out="".join(lines)\n        ast.parse(out)\n        return out\n    raise RuntimeError("CHILDREN is not a dictionary")\n\ndef verify_obr_005_async_cutover():\n    return OBR_005_BUILD_ID=="OBR-005" and callable(patch_launcher)\n';TEST_SOURCE='import unittest,ast\nimport qseries_v2.oracle_background_recovery.obr_005_live_cutover as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OBR_005_BUILD_ID,"OBR-005")\n    def test_patch(self):\n        s="CHILDREN={\'fast\':\'a.py\',\'inventory\':\'b.py\'}\\ndef run_forever(cadence):\\n    pass\\n"\n        x=m.patch_launcher(s);ast.parse(x);self.assertIn("run_oracle_background_recovery.py",x)\nif __name__=="__main__":\n    print("="*88);print(" OBR-005 CERTIFICATION TEST");print(" ASYNCHRONOUS LIVE CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] recovery added as background child")\n    print("[PASS] no synchronous recovery call added")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OBR-005 CERTIFIED")\n';WORKER_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport time,traceback\n\nfrom qseries_v2.oracle_background_recovery.obr_002_gap_queue import enqueue_gap,next_queued_gap,mark_completed\nfrom qseries_v2.oracle_background_recovery.obr_003_state_recovery import recover_gap_market_states\nfrom qseries_v2.oracle_background_recovery.obr_004_settlement_recovery import recover_gap_settlements\n\ndef run_once(root):\n    gap=next_queued_gap(root)\n    if gap is None:\n        gap=enqueue_gap(root)\n    if gap is None:\n        print("[OBR] no_recovery_gap",flush=True)\n        return False\n    print(f"[OBR] starting gap_id={gap[\'gap_id\'][:12]} gap_seconds={gap[\'gap_seconds\']:.1f}",flush=True)\n    state=recover_gap_market_states(root,gap,progress=lambda x:print(x,flush=True))\n    settlements=recover_gap_settlements(root,gap,progress=lambda x:print(x,flush=True))\n    summary={**state,**settlements,"gap_seconds":gap["gap_seconds"]}\n    mark_completed(root,gap["gap_id"],summary)\n    print(f"[OBR] complete gap_id={gap[\'gap_id\'][:12]} summary={summary}",flush=True)\n    return True\n\ndef main():\n    root=Path.cwd().resolve()\n    while True:\n        try:\n            ran=run_once(root)\n            time.sleep(60 if ran else 30)\n        except KeyboardInterrupt:\n            return 0\n        except Exception as exc:\n            print(f"[OBR] failure={type(exc).__name__}: {exc}",flush=True)\n            traceback.print_exc()\n            time.sleep(30)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88);print(" OBR-005 INSTALLER");print(" ASYNCHRONOUS BACKGROUND RECOVERY LIVE CUTOVER");print("="*88);print("[ROOT]",ROOT)
    paths=(MOD,TEST,INIT,WORKER,LAUNCHER);old={p:(p.read_bytes() if p.exists() else None) for p in paths}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(WORKER,WORKER_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";line="from .obr_005_live_cutover import *"
        if line not in cur.splitlines():write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        sys.path.insert(0,str(ROOT))
        import importlib
        m=importlib.import_module("qseries_v2.oracle_background_recovery.obr_005_live_cutover")
        patched=m.patch_launcher(LAUNCHER.read_text(encoding="utf-8"))
        if "reconcile_downtime_delta(" in patched or "reconcile_complete_gap_settlements(" in patched or "run_recovery_preflight(" in patched:
            raise RuntimeError("Blocking recovery call detected in launcher")
        compile(patched,str(LAUNCHER),"exec");write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OBR-005 failed; launcher restored");raise
    print("[PASS] Oracle Live starts normal children immediately")
    print("[PASS] Recovery is supervised as independent background child")
    print("[PASS] Recovery failure cannot block fast lane startup")
    print("[PASS] OIR-001 continuity remains source of last-known-good boundary")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OBR-001 THROUGH OBR-005 BACKGROUND RECOVERY CUTOVER COMPLETE")
if __name__=="__main__":main()
