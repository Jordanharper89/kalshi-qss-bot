from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_026_durable_calibration_ledger.py"
TEST_PATH=ROOT/"test_olr_026_durable_calibration_ledger.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport json,os\nfrom hashlib import sha256\n\nOLR_026_BUILD_ID="OLR-026"\nOLR_026_REVISION="OLR_026_DURABLE_CALIBRATION_LEDGER_V1"\n\n@dataclass(frozen=True)\nclass DurableCalibrationRecord:\n    record_id:str\n    market_ticker:str\n    probability:float\n    outcome:float\n    brier_score:float\n    absolute_error:float\n    source_key:str\n    source_observation_id:str\n    settlement_hash:str\n\ndef build_durable_calibration_record(calibration_record,source_observation_id="",settlement_hash=""):\n    payload="|".join((\n        str(calibration_record.market_ticker),\n        f"{float(calibration_record.probability):.12f}",\n        f"{float(calibration_record.outcome):.1f}",\n        str(source_observation_id),\n        str(settlement_hash),\n    ))\n    rid=sha256(payload.encode()).hexdigest()\n    return DurableCalibrationRecord(\n        rid,\n        str(calibration_record.market_ticker),\n        float(calibration_record.probability),\n        float(calibration_record.outcome),\n        float(calibration_record.brier_score),\n        float(calibration_record.absolute_error),\n        str(calibration_record.source_key),\n        str(source_observation_id),\n        str(settlement_hash),\n    )\n\ndef load_calibration_ledger(path):\n    p=Path(path)\n    if not p.is_file():return {}\n    data=json.loads(p.read_text(encoding="utf-8"))\n    return {k:DurableCalibrationRecord(**v) for k,v in data.items()}\n\ndef save_calibration_ledger(path,records):\n    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)\n    tmp=p.with_suffix(p.suffix+".tmp")\n    payload={k:asdict(v) for k,v in sorted(records.items())}\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,p)\n\ndef admit_calibration_record(records,record):\n    out=dict(records)\n    old=out.get(record.record_id)\n    if old is not None:\n        return out,False\n    out[record.record_id]=record\n    return out,True\n\ndef verify_olr_026_durable_calibration_ledger():\n    from qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import OutcomeCalibrationRecord\n    c=OutcomeCalibrationRecord("KX",.6,1,.16,.4,"p",True,False)\n    r=build_durable_calibration_record(c,"obs","settle")\n    x,a=admit_calibration_record({},r)\n    y,b=admit_calibration_record(x,r)\n    return a and not b and x==y and len(r.record_id)==64\n'
TEST_SOURCE='import tempfile,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import OutcomeCalibrationRecord\nfrom qseries_v2.oracle_learning_runtime.olr_026_durable_calibration_ledger import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_026_durable_calibration_ledger())\n    def test_persistence(self):\n        c=OutcomeCalibrationRecord("KX",.7,1,.09,.3,"p",True,False)\n        r=build_durable_calibration_record(c,"obs","settle")\n        with tempfile.TemporaryDirectory() as d:\n            p=Path(d)/"ledger.json"\n            save_calibration_ledger(p,{r.record_id:r})\n            self.assertEqual(load_calibration_ledger(p)[r.record_id],r)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-026 CERTIFICATION TEST");print(" DURABLE CALIBRATION LEDGER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Durable idempotent calibration ledger certified")\n    print("[DONE] OLR-026 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-026 INSTALLER")
    print(" DURABLE CALIBRATION LEDGER")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_025_outcome_calibration_market_behavior_gate')
    verifier=getattr(upstream,'verify_olr_025_outcome_calibration_market_behavior_gate')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-025 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_026_durable_calibration_ledger import *"
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
        print("[ROLLBACK] OLR-026 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-026 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
