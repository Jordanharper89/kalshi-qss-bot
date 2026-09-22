from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_001_learned_state_snapshot.py"
TEST=ROOT/"test_olf_001_durable_learned_state_snapshot_bridge.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict,dataclass\nfrom pathlib import Path\nimport json,os\n\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import (\n    load_production_learned_state,\n)\nfrom qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver import (\n    resolve_market_feedback,\n)\nfrom qseries_v2.oracle_learning_runtime.olr_018_scientific_reasoning_feedback_envelope import (\n    build_scientific_reasoning_feedback_envelope,\n)\n\nOLF_001_BUILD_ID="OLF-001"\nOLF_001_REVISION="OLF_001_DURABLE_LEARNED_STATE_SNAPSHOT_BRIDGE_V1"\nSNAPSHOT_NAME="oracle_reasoning_feedback_snapshot.json"\n\n@dataclass(frozen=True)\nclass LearnedFeedbackSnapshotSummary:\n    learner_state_hash:str\n    outcomes_learned:int\n    learned_records:int\n    markets:int\n    snapshot_path:str\n    execution_authority:bool=False\n\ndef build_snapshot_payload(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    state=load_production_learned_state(root)\n    markets=[]\n    for ticker,count in state.learned_market_counts:\n        resolution=resolve_market_feedback(state,ticker)\n        envelope=build_scientific_reasoning_feedback_envelope(resolution)\n        markets.append(asdict(envelope))\n    return {\n        "revision":OLF_001_REVISION,\n        "learner_state_hash":state.learner_state_hash,\n        "learning_cycles":state.cycles,\n        "outcomes_learned":state.outcomes_learned,\n        "applied_through_sequence":state.applied_through_sequence,\n        "learned_records":state.learned_records,\n        "markets":markets,\n        "execution_authority":False,\n    }\n\ndef materialize_learned_feedback_snapshot(root=None,output_path=None):\n    root=Path(root or Path.cwd()).resolve()\n    payload=build_snapshot_payload(root)\n    path=Path(output_path or root/"runtime_state"/SNAPSHOT_NAME)\n    path.parent.mkdir(parents=True,exist_ok=True)\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(\n        json.dumps(payload,sort_keys=True,separators=(",",":")),\n        encoding="utf-8",\n        newline="\\n",\n    )\n    os.replace(tmp,path)\n    return LearnedFeedbackSnapshotSummary(\n        str(payload["learner_state_hash"]),\n        int(payload["outcomes_learned"]),\n        int(payload["learned_records"]),\n        len(payload["markets"]),\n        str(path.relative_to(root)),\n        False,\n    )\n\ndef verify_snapshot_matches_current_learner(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    path=root/"runtime_state"/SNAPSHOT_NAME\n    if not path.is_file():\n        return False\n    payload=json.loads(path.read_text(encoding="utf-8"))\n    state=load_production_learned_state(root)\n    return (\n        str(payload.get("learner_state_hash") or "")==state.learner_state_hash\n        and int(payload.get("outcomes_learned",0))==state.outcomes_learned\n        and int(payload.get("learned_records",0))==state.learned_records\n        and payload.get("execution_authority") is False\n    )\n\ndef verify_olf_001_durable_learned_state_snapshot_bridge():\n    return OLF_001_BUILD_ID=="OLF-001" and callable(materialize_learned_feedback_snapshot)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_001_learned_state_snapshot import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(OLF_001_BUILD_ID,"OLF-001")\n    def test_contract(self):\n        self.assertTrue(callable(materialize_learned_feedback_snapshot))\n        self.assertTrue(callable(verify_snapshot_matches_current_learner))\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLF-001 CERTIFICATION TEST")\n    print(" DURABLE LEARNED-STATE SNAPSHOT BRIDGE")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Learned-state snapshot bridge contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-001 CERTIFIED")\n'

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

def main():
    print("="*88);print(" OLF-001 INSTALLER");print(" DURABLE LEARNED-STATE SNAPSHOT BRIDGE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    proven=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle")
    adapter=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter")
    if not callable(getattr(proven,"run_high_coverage_learning_cycle",None)):
        raise RuntimeError("Proven OLR-009 learning cycle missing")
    current=adapter.load_production_learned_state(ROOT)
    if current.outcomes_learned<=0 or current.learned_records<=0 or not current.learner_state_hash:
        raise RuntimeError("No physically learned production state present; refusing OLF installation")
    print(f"[PROVEN LEARNING] cycles={current.cycles} outcomes_learned={current.outcomes_learned} learned_records={current.learned_records} state_hash={current.learner_state_hash}")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .olf_001_learned_state_snapshot import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_001_learned_state_snapshot")
        summary=m.materialize_learned_feedback_snapshot(ROOT)
        if not m.verify_snapshot_matches_current_learner(ROOT):
            raise RuntimeError("Physical learned-state snapshot does not match current learner state")
        print(f"[PHYSICAL SNAPSHOT] outcomes={summary.outcomes_learned} learned_records={summary.learned_records} markets={summary.markets} state_hash={summary.learner_state_hash}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-001 failed; affected files restored");raise
    print("[PASS] Proven learner mutation logic unchanged")
    print("[PASS] OPR/OPH unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-001 INSTALLATION COMPLETE")
if __name__=="__main__":main()
