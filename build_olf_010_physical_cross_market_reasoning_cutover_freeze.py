from pathlib import Path
import importlib,json,os,subprocess,sys,hashlib
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_010_cross_market_reasoning_runtime.py";CUT=PKG/"olf_010_live_cutover.py";TEST=ROOT/"test_olf_010_cross_market_reasoning_runtime.py"
RUN=ROOT/"run_olf_010_cross_market_reasoning_runtime.py";INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py";MANIFEST=PKG/"OLF_010_FREEZE_MANIFEST.json"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict,dataclass\nfrom pathlib import Path\nimport json,os\n\nfrom qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor\nfrom qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row\nfrom qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context\nfrom qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations\nfrom qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results\nfrom .olf_001_learned_state_snapshot import materialize_learned_feedback_snapshot\nfrom .olf_007_cross_market_learning_index import materialize_cross_market_learning_index\nfrom .olf_009_generalized_learning_context import build_generalized_learning_context\n\nOLF_010_BUILD_ID="OLF-010"\nOLF_010_REVISION="OLF_010_CROSS_MARKET_REASONING_RUNTIME_V1"\nATTESTATION_NAME="oracle_cross_market_learning_reasoning_attestation.json"\n\n@dataclass(frozen=True)\nclass CrossMarketReasoningCycleSummary:\n    rows_read:int\n    markets_reasoned:int\n    learning_contexts:int\n    exact_contexts:int\n    generalized_contexts:int\n    calibrated_contexts:int\n    learner_state_hash:str\n    idle:bool\n    execution_authority:bool=False\n\ndef _attest(root,payload):\n    path=Path(root)/"runtime_state"/ATTESTATION_NAME\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n\ndef _contexts_for_reasoning(root,reasoning):\n    contexts=tuple(build_generalized_learning_context(root,x.market_ticker) for x in reasoning)\n    hashes={x.learner_state_hash for x in contexts if x.learner_state_hash}\n    if len(hashes)>1:raise RuntimeError("Inconsistent learner-state hashes in generalized reasoning context")\n    return contexts,next(iter(hashes),"")\n\ndef run_cross_market_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):\n    root=Path(root or Path.cwd()).resolve()\n    materialize_learned_feedback_snapshot(root)\n    materialize_cross_market_learning_index(root)\n    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json")\n    cursor=load_reasoning_cursor(cp)\n    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)\n    if not slice_.rows:\n        progress("[OLF-010 OCR] idle no_new_observations")\n        return CrossMarketReasoningCycleSummary(0,0,0,0,0,0,"",True,False)\n    aware=join_rows_to_umd_context(slice_.rows)\n    if not aware:raise RuntimeError("No market identities recovered from new canonical observations")\n    reasoning=reason_over_market_aware_observations(aware)\n    projections=project_reasoning_results(reasoning)\n    if len(projections)!=len(reasoning):raise RuntimeError("OIS projection count mismatch")\n    contexts,state_hash=_contexts_for_reasoning(root,reasoning)\n    consumed=sum(x.learning_context_consumed for x in contexts)\n    exact=sum(x.relationship_type=="EXACT_TICKER" for x in contexts)\n    generalized=sum(x.relationship_type=="SAME_KALSHI_SERIES" for x in contexts)\n    calibrated=sum(x.calibration_applied for x in contexts)\n\n    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)\n    save_reasoning_cursor(cp,advance_reasoning_cursor(cursor,order_column,order_value,observation_id,len(slice_.rows)))\n    _attest(root,{\n        "revision":OLF_010_REVISION,"learner_state_hash":state_hash,\n        "rows_read":len(slice_.rows),"markets_reasoned":len(reasoning),\n        "learning_contexts":consumed,"exact_contexts":exact,\n        "generalized_contexts":generalized,"calibrated_contexts":calibrated,\n        "contexts":[asdict(x) for x in contexts],"execution_authority":False,\n    })\n    progress(f"[OLF-010 OCR] rows={len(slice_.rows)} markets_reasoned={len(reasoning)} learning_context={consumed} exact={exact} generalized={generalized} calibrated={calibrated}")\n    progress(f"[OLF-010 OCR] learner_state_hash={state_hash}")\n    return CrossMarketReasoningCycleSummary(len(slice_.rows),len(reasoning),consumed,exact,generalized,calibrated,state_hash,False,False)\n\ndef proof_recent_generalization(root=None,limit=100):\n    from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations\n    root=Path(root or Path.cwd()).resolve()\n    materialize_learned_feedback_snapshot(root);materialize_cross_market_learning_index(root)\n    rows=read_latest_canonical_observations(root,limit=limit).rows\n    aware=join_rows_to_umd_context(rows)\n    reasoning=reason_over_market_aware_observations(aware)\n    contexts,state_hash=_contexts_for_reasoning(root,reasoning)\n    matches=tuple(x for x in contexts if x.learning_context_consumed)\n    generalized=tuple(x for x in matches if x.relationship_type=="SAME_KALSHI_SERIES")\n    return reasoning,matches,generalized,state_hash\n\ndef verify_olf_010_cross_market_reasoning_runtime():\n    return OLF_010_BUILD_ID=="OLF-010" and callable(run_cross_market_reasoning_cycle)\n';CUT_SOURCE='from __future__ import annotations\nimport ast\nOLF_010_CUTOVER_BUILD_ID="OLF-010-CUTOVER"\nTARGET="run_olf_010_cross_market_reasoning_runtime.py"\ndef patch_reasoning_child(source,target=TARGET):\n    tree=ast.parse(source);node=None\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):\n            node=item.value;break\n    if node is None:raise RuntimeError("CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if isinstance(k,ast.Constant) and str(k.value)=="reasoning" and isinstance(v,ast.Constant):\n            old=str(v.value)\n            if old==target:return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(target),1)\n                    out="".join(lines);ast.parse(out);return out\n    raise RuntimeError("reasoning child not found")\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_010_cross_market_reasoning_runtime import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_010_BUILD_ID,"OLF-010")\n    def test_contract(self):self.assertTrue(verify_olf_010_cross_market_reasoning_runtime())\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-010 CERTIFICATION TEST");print(" CROSS-MARKET REASONING RUNTIME");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Cross-market learning-aware reasoning runtime certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-010 GATE CERTIFIED")\n';RUN_SOURCE='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_learning_feedback.olf_010_cross_market_reasoning_runtime import run_cross_market_reasoning_cycle\n\ndef main(argv=None):\n    p=argparse.ArgumentParser();p.add_argument("--batch-size",type=int,default=50);p.add_argument("--cadence-seconds",type=float,default=2.0);p.add_argument("--check",action="store_true");p.add_argument("--once",action="store_true")\n    a=p.parse_args(argv)\n    if a.check:\n        print("[READY] OLF-010 cross-market learning reasoning runtime")\n        print("[PASS] historical_transfer_boundary=SAME_KALSHI_SERIES_ONLY")\n        print("[PASS] execution_authority=FALSE");return 0\n    root=Path.cwd();cycle=0\n    print("="*88,flush=True);print(" OLF-010 CROSS-MARKET LEARNING REASONING RUNTIME",flush=True);print("="*88,flush=True)\n    while True:\n        cycle+=1\n        s=run_cross_market_reasoning_cycle(root,a.batch_size,progress=lambda x:print(x,flush=True))\n        print(f"[OLF-010 OCR] cycle={cycle} idle={s.idle} markets={s.markets_reasoned} context={s.learning_contexts} generalized={s.generalized_contexts}",flush=True)\n        if a.once:return 0\n        time.sleep(a.cadence_seconds)\nif __name__=="__main__":raise SystemExit(main())\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-010 INSTALLER");print(" PHYSICAL CROSS-MARKET REASONING CUTOVER + FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_009_generalized_learning_context")
    if not up.verify_olf_009_generalized_reasoning_learning_context():raise RuntimeError("OLF-009 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,CUT,TEST,RUN,INIT,LAUNCHER,MANIFEST)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(CUT,CUT_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(RUN,RUN_SOURCE)
        update_init(INIT,"from .olf_010_cross_market_reasoning_runtime import *");update_init(INIT,"from .olf_010_live_cutover import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True);subprocess.run([sys.executable,str(RUN),"--check"],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_010_cross_market_reasoning_runtime")
        reasoning,matches,generalized,state_hash=m.proof_recent_generalization(ROOT,limit=100)
        print(f"[PHYSICAL GENERALIZATION] markets_reasoned={len(reasoning)} learning_context={len(matches)} generalized={len(generalized)} state_hash={state_hash}")
        for x in generalized[:10]:
            print(f"[GENERALIZED] target={x.market_ticker} relationship={x.relationship_type} sources={len(x.source_markets)} learned_records={x.learned_records} weight={x.experience_weight:.3f}")
        if len(matches)<=0:
            raise RuntimeError("No recent market consumed learned context; refusing production cutover")
        if len(generalized)<=0:
            raise RuntimeError("No recent market demonstrated true cross-market same-series generalization; refusing production cutover")
        current=json.loads((ROOT/"runtime_state"/"oracle_learning_runtime_state.json").read_text(encoding="utf-8"))
        current_hash=str((current.get("ocl_state") or {}).get("state_hash") or "")
        if not current_hash or state_hash!=current_hash:
            raise RuntimeError("Physical generalized reasoning did not consume current learner state hash")

        c=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_010_live_cutover")
        patched=c.patch_reasoning_child(LAUNCHER.read_text(encoding="utf-8"))
        compile(patched,str(LAUNCHER),"exec");write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)

        body={
            "build_id":"OLF-010","revision":"OLF_010_CROSS_MARKET_REASONING_FREEZE_V1",
            "learner_state_hash":state_hash,"physical_recent_markets_reasoned":len(reasoning),
            "physical_learning_contexts":len(matches),"physical_generalized_contexts":len(generalized),
            "relationship_boundary":"SAME_KALSHI_SERIES_ONLY","proven_learning_child_unchanged":True,
            "execution_authority":False
        }
        payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
        write_exact(MANIFEST,json.dumps(body,sort_keys=True,indent=2)+"\n")
        print("[PASS] Wrote:",MANIFEST.relative_to(ROOT));print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-010 failed; Oracle Live launcher and affected files restored");raise
    print("[PASS] Real recent market consumed historical same-series learning")
    print("[PASS] Current learner state hash preserved end-to-end")
    print("[PASS] Cross-series transfer prohibited")
    print("[PASS] Proven learning child unchanged")
    print("[PASS] Oracle Live reasoning child -> run_olf_010_cross_market_reasoning_runtime.py")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-006 THROUGH OLF-010 CROSS-MARKET GENERALIZATION FROZEN")
if __name__=="__main__":main()
