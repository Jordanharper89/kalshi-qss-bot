from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_041_learning_health_model.py"
TEST_PATH=ROOT/"test_olr_041_learning_health_model.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nOLR_041_BUILD_ID="OLR-041"\nOLR_041_REVISION="OLR_041_LEARNING_HEALTH_MODEL_V1"\n\n@dataclass(frozen=True)\nclass LearningHealthSnapshot:\n    learning_state_present:bool\n    calibration_state_present:bool\n    calibration_ledger_present:bool\n    feedback_snapshot_present:bool\n    learning_cycles:int\n    outcomes_learned:int\n    calibration_cycles:int\n    calibration_records:int\n    mature_markets:int\n    health:str\n    reason:str\n    execution_authority:bool=False\n\ndef _read(path):\n    p=Path(path)\n    if not p.is_file():\n        return {}\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return {}\n\ndef inspect_learning_health(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    learning_path=root/"runtime_state"/"oracle_learning_runtime_state.json"\n    calibration_state_path=root/"runtime_state"/"oracle_calibration_ingestion_state.json"\n    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"\n    feedback_path=root/"runtime_state"/"oracle_live_reasoning_feedback.json"\n\n    learning=_read(learning_path)\n    calibration=_read(calibration_state_path)\n    ledger=_read(ledger_path)\n    feedback=_read(feedback_path)\n\n    learning_present=learning_path.is_file()\n    calibration_present=calibration_state_path.is_file()\n    ledger_present=ledger_path.is_file()\n    feedback_present=feedback_path.is_file()\n\n    learning_cycles=int(learning.get("cycles",0)) if isinstance(learning,dict) else 0\n    outcomes_learned=int(learning.get("outcomes_learned",0)) if isinstance(learning,dict) else 0\n    calibration_cycles=int(calibration.get("cycles_completed",0)) if isinstance(calibration,dict) else 0\n    calibration_records=len(ledger) if isinstance(ledger,dict) else 0\n    markets=feedback.get("markets",[]) if isinstance(feedback,dict) else []\n    mature_markets=sum(1 for r in markets if isinstance(r,dict) and r.get("mature") is True)\n\n    if not learning_present:\n        health="NOT_READY";reason="learning_state_missing"\n    elif not calibration_state_path.parent.exists():\n        health="DEGRADED";reason="runtime_state_directory_missing"\n    elif outcomes_learned==0 and calibration_records==0:\n        health="HEALTHY_WAITING_FOR_ELIGIBLE_OUTCOMES";reason="no_eligible_learning_yet"\n    elif calibration_records==0:\n        health="HEALTHY_LEARNING_NO_CALIBRATION_YET";reason="learning_exists_but_no_defensible_calibration_records"\n    elif mature_markets==0:\n        health="HEALTHY_ACCUMULATING_HISTORY";reason="calibration_history_not_mature"\n    else:\n        health="HEALTHY_MATURE";reason="mature_learning_available"\n\n    return LearningHealthSnapshot(\n        learning_present,calibration_present,ledger_present,feedback_present,\n        learning_cycles,outcomes_learned,calibration_cycles,calibration_records,\n        mature_markets,health,reason,False\n    )\n\ndef verify_olr_041_learning_health_model():\n    x=inspect_learning_health(Path("__missing_olr_health_root__"))\n    return x.health=="NOT_READY" and x.execution_authority is False\n'
TEST_SOURCE='import tempfile,unittest,json\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_041_learning_health_model import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_041_learning_health_model())\n    def test_waiting_is_not_failure(self):\n        with tempfile.TemporaryDirectory() as d:\n            r=Path(d);(r/"runtime_state").mkdir()\n            (r/"runtime_state"/"oracle_learning_runtime_state.json").write_text(json.dumps({"cycles":5,"outcomes_learned":0}))\n            x=inspect_learning_health(r)\n            self.assertEqual(x.health,"HEALTHY_WAITING_FOR_ELIGIBLE_OUTCOMES")\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-041 CERTIFICATION TEST");print(" LEARNING HEALTH MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Healthy-zero-learning state distinguished from runtime failure")\n    print("[DONE] OLR-041 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-041 INSTALLER")
    print(" LEARNING HEALTH MODEL")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_040_learning_consumption_maturity_gate')
    verifier=getattr(upstream,'verify_olr_040_learning_consumption_maturity_gate')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-040 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_041_learning_health_model import *"
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
        print("[ROLLBACK] OLR-041 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-041 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
