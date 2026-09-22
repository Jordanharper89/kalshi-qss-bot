from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_036_live_feedback_read_model.py"
TEST_PATH=ROOT/"test_olr_036_live_feedback_read_model.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nOLR_036_BUILD_ID="OLR-036"\nOLR_036_REVISION="OLR_036_LIVE_FEEDBACK_READ_MODEL_V1"\n\n@dataclass(frozen=True)\nclass LiveCalibrationFeedback:\n    market_ticker:str\n    samples:int\n    calibration_bias:float\n    mean_brier_score:float\n    reliability_weight:float\n    mature:bool\n    behavior_class:str\n    stable:bool\n    execution_authority:bool=False\n\ndef load_live_feedback_snapshot(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    path=root/"runtime_state"/"oracle_live_reasoning_feedback.json"\n    if not path.is_file():\n        return {}\n    data=json.loads(path.read_text(encoding="utf-8"))\n    out={}\n    for row in data.get("markets",[]):\n        if not isinstance(row,dict):continue\n        ticker=str(row.get("market_ticker") or "")\n        if not ticker:continue\n        out[ticker]=LiveCalibrationFeedback(\n            ticker,\n            int(row.get("samples",0)),\n            float(row.get("calibration_bias",0.0)),\n            float(row.get("mean_brier_score",0.25)),\n            float(row.get("reliability_weight",0.0)),\n            bool(row.get("mature",False)),\n            str(row.get("behavior_class") or "insufficient_history"),\n            bool(row.get("stable",False)),\n            False,\n        )\n    return out\n\ndef verify_olr_036_live_feedback_read_model():\n    return load_live_feedback_snapshot(Path("__missing__"))=={}\n'
TEST_SOURCE='import tempfile,unittest,json\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_036_live_feedback_read_model())\n    def test_read(self):\n        with tempfile.TemporaryDirectory() as d:\n            r=Path(d);(r/"runtime_state").mkdir()\n            (r/"runtime_state"/"oracle_live_reasoning_feedback.json").write_text(json.dumps({"markets":[{"market_ticker":"KX","samples":5,"mature":True}]}))\n            self.assertTrue(load_live_feedback_snapshot(r)["KX"].mature)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-036 CERTIFICATION TEST");print(" LIVE FEEDBACK READ MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Read-only live calibration feedback model certified")\n    print("[DONE] OLR-036 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-036 INSTALLER");print(" LIVE FEEDBACK READ MODEL");print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_035_production_calibration_supervision_gate')
    if getattr(upstream,'verify_olr_035_production_calibration_supervision_gate')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-035 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_036_live_feedback_read_model import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-036 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-036 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
