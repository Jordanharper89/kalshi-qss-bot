from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_029_live_reasoning_feedback_projection.py"
TEST_PATH=ROOT/"test_olr_029_live_reasoning_feedback_projection.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport json,os\nfrom .olr_026_durable_calibration_ledger import load_calibration_ledger\nfrom .olr_027_accumulated_calibration_state import accumulate_market_calibration\nfrom .olr_028_market_behavior_history import classify_market_behavior\n\nOLR_029_BUILD_ID="OLR-029"\nOLR_029_REVISION="OLR_029_LIVE_REASONING_FEEDBACK_PROJECTION_V1"\n\n@dataclass(frozen=True)\nclass LiveReasoningFeedbackProjection:\n    markets:int\n    calibration_records:int\n    mature_markets:int\n    output_path:str\n    execution_authority:bool=False\n\ndef materialize_live_reasoning_feedback(root=None,output_path=None,min_samples=5):\n    root=Path(root or Path.cwd()).resolve()\n    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"\n    ledger=load_calibration_ledger(ledger_path)\n    records=tuple(ledger.values())\n    tickers=sorted({r.market_ticker for r in records})\n    rows=[]\n    mature=0\n    for ticker in tickers:\n        state=accumulate_market_calibration(records,ticker,min_samples=min_samples)\n        hist=classify_market_behavior(state)\n        if state.mature:mature+=1\n        rows.append({\n            "market_ticker":ticker,\n            "samples":state.samples,\n            "mean_probability":state.mean_probability,\n            "empirical_yes_rate":state.empirical_yes_rate,\n            "mean_brier_score":state.mean_brier_score,\n            "calibration_bias":state.calibration_bias,\n            "reliability_weight":state.reliability_weight,\n            "mature":state.mature,\n            "behavior_class":hist.behavior_class,\n            "stable":hist.stable,\n            "execution_authority":False,\n        })\n    payload={\n        "revision":OLR_029_REVISION,\n        "calibration_records":len(records),\n        "markets":rows,\n        "execution_authority":False,\n    }\n    path=Path(output_path or root/"runtime_state"/"oracle_live_reasoning_feedback.json")\n    path.parent.mkdir(parents=True,exist_ok=True)\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n    return LiveReasoningFeedbackProjection(len(rows),len(records),mature,str(path.relative_to(root)),False)\n\ndef verify_olr_029_live_reasoning_feedback_projection():\n    import tempfile\n    with tempfile.TemporaryDirectory() as d:\n        x=materialize_live_reasoning_feedback(Path(d))\n        return x.markets==0 and x.calibration_records==0 and not x.execution_authority\n'
TEST_SOURCE='import tempfile,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_029_live_reasoning_feedback_projection())\n    def test_snapshot_exists(self):\n        with tempfile.TemporaryDirectory() as d:\n            r=Path(d);x=materialize_live_reasoning_feedback(r)\n            self.assertTrue((r/"runtime_state"/"oracle_live_reasoning_feedback.json").is_file())\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-029 CERTIFICATION TEST");print(" LIVE REASONING FEEDBACK PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Atomic live reasoning feedback projection certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-029 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_029_live_reasoning_feedback_projection.py'
EXTRA_SOURCE_1='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import materialize_live_reasoning_feedback\n\ndef main():\n    p=argparse.ArgumentParser();p.add_argument("--cadence-seconds",type=float,default=15.0);p.add_argument("--once",action="store_true");a=p.parse_args()\n    if a.cadence_seconds<=0:raise SystemExit("invalid cadence")\n    root=Path.cwd()\n    print("="*72,flush=True);print(" OLR-029 LIVE REASONING FEEDBACK PROJECTION RUNTIME",flush=True);print("="*72,flush=True)\n    cycles=0\n    try:\n        while True:\n            s=materialize_live_reasoning_feedback(root);cycles+=1\n            print(f"[CALIBRATION FEEDBACK] cycle={cycles} records={s.calibration_records} markets={s.markets} mature_markets={s.mature_markets} snapshot={s.output_path} execution_authority=FALSE",flush=True)\n            if a.once:return 0\n            time.sleep(a.cadence_seconds)\n    except KeyboardInterrupt:\n        print("\\n[STOP] Calibration feedback runtime stopped by operator.",flush=True);return 0\n\nif __name__=="__main__":raise SystemExit(main())\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-029 INSTALLER")
    print(" LIVE REASONING FEEDBACK PROJECTION")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_028_market_behavior_history')
    verifier=getattr(upstream,'verify_olr_028_market_behavior_history')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-028 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_029_live_reasoning_feedback_projection import *"
        if export_line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-029 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-029 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
