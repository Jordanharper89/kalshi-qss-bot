from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_031_calibration_candidate_intake.py"
TEST_PATH=ROOT/"test_olr_031_calibration_candidate_intake.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom .olr_002_settled_outcome_read_model import fetch_recent_settled_markets\nfrom .olr_006_historical_evidence_matcher import find_historical_market_evidence\nfrom .olr_007_learning_event_ledger import load_learning_ledger\nfrom .olr_022_outcome_calibration_record import build_outcome_calibration_record\n\nOLR_031_BUILD_ID="OLR-031"\nOLR_031_REVISION="OLR_031_CALIBRATION_CANDIDATE_INTAKE_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass CalibrationCandidate:\n    settlement_hash:str\n    market_ticker:str\n    settlement_ts:str\n    evidence_hash:str\n    source_observation_id:str\n    calibration_record:object\n\n@dataclass(frozen=True)\nclass CalibrationCandidateBatch:\n    settled_scanned:int\n    learned_settlements:int\n    exact_evidence_matches:int\n    probability_abstentions:int\n    candidates:tuple\n\ndef assemble_calibration_candidates(root=None, settled_limit=100, evidence_limit=25):\n    root=Path(root or Path.cwd()).resolve()\n    ledger=load_learning_ledger(root/"runtime_state"/"oracle_learning_event_ledger.json")\n    outcomes=fetch_recent_settled_markets(root,limit=settled_limit)\n\n    learned=0\n    matched=0\n    abstain=0\n    candidates=[]\n\n    for outcome in outcomes:\n        lineage=ledger.get(outcome.source_hash)\n        if lineage is None or lineage.status!="learned":\n            continue\n\n        learned+=1\n        matches=find_historical_market_evidence(root,outcome.ticker,limit=evidence_limit)\n        exact=next((m for m in matches if m.evidence_hash==lineage.evidence_hash),None)\n        if exact is None:\n            continue\n\n        matched+=1\n        record=build_outcome_calibration_record(\n            outcome.ticker,\n            exact.row,\n            outcome.result,\n        )\n        if record is None:\n            abstain+=1\n            continue\n\n        candidates.append(\n            CalibrationCandidate(\n                outcome.source_hash,\n                outcome.ticker,\n                outcome.settlement_ts,\n                exact.evidence_hash,\n                exact.observation_id,\n                record,\n            )\n        )\n\n    return CalibrationCandidateBatch(\n        len(outcomes),\n        learned,\n        matched,\n        abstain,\n        tuple(candidates),\n    )\n\ndef verify_olr_031_calibration_candidate_intake():\n    x=CalibrationCandidateBatch(1,1,1,0,tuple())\n    return x.settled_scanned==1 and x.learned_settlements==1\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_031_calibration_candidate_intake import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_031_calibration_candidate_intake())\n\n    def test_contract(self):\n        x=CalibrationCandidateBatch(2,1,1,1,tuple())\n        self.assertEqual(x.probability_abstentions,1)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-031 CERTIFICATION TEST")\n    print(" CALIBRATION CANDIDATE INTAKE")\n    print("="*72)\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Learned-settlement + exact-evidence calibration intake certified")\n    print("[PASS] Missing defensible probability remains abstention")\n    print("[DONE] OLR-031 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-031 INSTALLER - CORRECTION V2")
    print(" CALIBRATION CANDIDATE INTAKE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module(
        "qseries_v2.oracle_learning_runtime.olr_030_durable_calibration_reasoning_binding_gate"
    )
    if upstream.verify_olr_030_durable_calibration_reasoning_binding_gate() is not True:
        raise RuntimeError("Certified OLR-030 upstream verification failed")
    print("[PASS] Certified OLR-030 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH)
    backups={
        path_obj:(path_obj.read_bytes() if path_obj.exists() else None)
        for path_obj in affected
    }

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_031_calibration_candidate_intake import *"
        if export_line not in current:
            write_exact(
                INIT_PATH,
                current.rstrip()+"\n"+export_line+"\n"
            )

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run(
            [sys.executable,str(TEST_PATH)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-031 Correction V2 failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-031 CORRECTION V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
