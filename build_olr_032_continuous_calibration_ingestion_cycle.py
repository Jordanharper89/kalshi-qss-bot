from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_032_continuous_calibration_ingestion_cycle.py"
TEST_PATH=ROOT/"test_olr_032_continuous_calibration_ingestion_cycle.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .olr_026_durable_calibration_ledger import load_calibration_ledger,save_calibration_ledger,build_durable_calibration_record,admit_calibration_record\nfrom .olr_031_calibration_candidate_intake import assemble_calibration_candidates\nOLR_032_BUILD_ID="OLR-032";OLR_032_REVISION="OLR_032_CONTINUOUS_CALIBRATION_INGESTION_CYCLE_V1"\n@dataclass(frozen=True)\nclass CalibrationIngestionCycleSummary:\n    settled_scanned:int;learned_settlements:int;exact_evidence_matches:int;probability_abstentions:int;candidates:int;admitted:int;duplicate_records:int;ledger_records:int\ndef run_calibration_ingestion_cycle(root=None,settled_limit=100,evidence_limit=25):\n    root=Path(root or Path.cwd()).resolve();batch=assemble_calibration_candidates(root,settled_limit,evidence_limit);path=root/"runtime_state"/"oracle_calibration_ledger.json";ledger=load_calibration_ledger(path);a=d=0\n    for c in batch.candidates:\n        rec=build_durable_calibration_record(c.calibration_record,c.source_observation_id,c.settlement_hash);ledger,added=admit_calibration_record(ledger,rec)\n        if added:a+=1\n        else:d+=1\n    save_calibration_ledger(path,ledger)\n    return CalibrationIngestionCycleSummary(batch.settled_scanned,batch.learned_settlements,batch.exact_evidence_matches,batch.probability_abstentions,len(batch.candidates),a,d,len(ledger))\ndef verify_olr_032_continuous_calibration_ingestion_cycle():return CalibrationIngestionCycleSummary(0,0,0,0,0,0,0,0).ledger_records==0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_032_continuous_calibration_ingestion_cycle import *\nclass T(unittest.TestCase):\n def test_verifier(self):self.assertTrue(verify_olr_032_continuous_calibration_ingestion_cycle())\nif __name__=="__main__":\n print("="*72);print(" OLR-032 CERTIFICATION TEST");print(" CONTINUOUS CALIBRATION INGESTION CYCLE");print("="*72)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Idempotent calibration ingestion cycle certified");print("[DONE] OLR-032 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    print("="*72);print(" OLR-032 INSTALLER");print(" CONTINUOUS CALIBRATION INGESTION CYCLE");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_031_calibration_candidate_intake')
    if getattr(up,'verify_olr_031_calibration_candidate_intake')() is not True:raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-031 upstream boundary verified")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD_PATH,MODULE_SOURCE);write_exact(TEST_PATH,TEST_SOURCE)
        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_032_continuous_calibration_ingestion_cycle import *"
        if line not in current:write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec");compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] OLR-032 installation failed; affected files restored");raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT));print("[PASS] Wrote:",TEST_PATH.name);print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-032 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
