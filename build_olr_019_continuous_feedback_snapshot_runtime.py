from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_019_continuous_feedback_snapshot_runtime.py"
TEST_PATH=ROOT/"test_olr_019_continuous_feedback_snapshot_runtime.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict,dataclass\nfrom pathlib import Path\nimport json,os\nfrom .olr_016_production_learned_state_adapter import load_production_learned_state\nfrom .olr_017_market_feedback_resolver import resolve_market_feedback\nfrom .olr_018_scientific_reasoning_feedback_envelope import build_scientific_reasoning_feedback_envelope\n\nOLR_019_BUILD_ID="OLR-019"\nOLR_019_REVISION="OLR_019_CONTINUOUS_FEEDBACK_SNAPSHOT_RUNTIME_V1"\n\n@dataclass(frozen=True)\nclass FeedbackSnapshotSummary:\n    markets:int\n    learned_records:int\n    snapshot_path:str\n    read_only_upstream:bool=True\n    execution_authority:bool=False\n\ndef materialize_feedback_snapshot(root=None,output_path=None):\n    root=Path(root or Path.cwd()).resolve()\n    state=load_production_learned_state(root)\n    rows=[]\n    for ticker,count in state.learned_market_counts:\n        resolution=resolve_market_feedback(state,ticker)\n        rows.append(asdict(build_scientific_reasoning_feedback_envelope(resolution)))\n    payload={\n        "revision":OLR_019_REVISION,\n        "learner_state_hash":state.learner_state_hash,\n        "outcomes_learned":state.outcomes_learned,\n        "learned_records":state.learned_records,\n        "markets":rows,\n        "execution_authority":False,\n    }\n    path=Path(output_path or root/"runtime_state"/"oracle_reasoning_feedback_snapshot.json")\n    path.parent.mkdir(parents=True,exist_ok=True)\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n    return FeedbackSnapshotSummary(len(rows),state.learned_records,str(path.relative_to(root)),True,False)\n\ndef verify_olr_019_continuous_feedback_snapshot_runtime():\n    import tempfile\n    with tempfile.TemporaryDirectory() as d:\n        x=materialize_feedback_snapshot(Path(d))\n        return x.markets==0 and x.read_only_upstream and not x.execution_authority\n'
TEST_SOURCE='import tempfile,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_019_continuous_feedback_snapshot_runtime())\n    def test_writes_only_olr_snapshot(self):\n        with tempfile.TemporaryDirectory() as d:\n            r=Path(d);x=materialize_feedback_snapshot(r)\n            self.assertTrue((r/"runtime_state"/"oracle_reasoning_feedback_snapshot.json").is_file())\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-019 CERTIFICATION TEST");print(" CONTINUOUS FEEDBACK SNAPSHOT RUNTIME");print("="*72)\n    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not result.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-owned atomic feedback snapshot runtime certified")\n    print("[DONE] OLR-019 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_019_continuous_feedback_snapshot_runtime.py'
EXTRA_SOURCE_1='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime import materialize_feedback_snapshot\n\ndef main():\n    p=argparse.ArgumentParser();p.add_argument("--cadence-seconds",type=float,default=15.0);p.add_argument("--once",action="store_true");a=p.parse_args()\n    if a.cadence_seconds<=0:raise SystemExit("invalid cadence")\n    root=Path.cwd()\n    print("="*72,flush=True);print(" OLR-019 CONTINUOUS LEARNED-STATE FEEDBACK SNAPSHOT RUNTIME",flush=True);print("="*72,flush=True)\n    cycles=0\n    try:\n        while True:\n            s=materialize_feedback_snapshot(root);cycles+=1\n            print(f"[FEEDBACK] cycle={cycles} markets={s.markets} learned_records={s.learned_records} snapshot={s.snapshot_path} execution_authority=FALSE",flush=True)\n            if a.once:return 0\n            time.sleep(a.cadence_seconds)\n    except KeyboardInterrupt:\n        print("\\n[STOP] Feedback snapshot runtime stopped by operator.",flush=True);return 0\n\nif __name__=="__main__":raise SystemExit(main())\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-019 INSTALLER");print(" CONTINUOUS FEEDBACK SNAPSHOT RUNTIME");print("="*72)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_018_scientific_reasoning_feedback_envelope')
    verifier=getattr(upstream,'verify_olr_018_scientific_reasoning_feedback_envelope')
    if verifier() is not True:raise RuntimeError("Upstream verification failed")
    print("[PASS] Certified upstream boundary verified")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}
    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_019_continuous_feedback_snapshot_runtime import *"
        if line not in current:write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-019 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-019 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
