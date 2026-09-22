from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .olr_026_durable_calibration_ledger import load_calibration_ledger,save_calibration_ledger,build_durable_calibration_record,admit_calibration_record
from .olr_031_calibration_candidate_intake import assemble_calibration_candidates
OLR_032_BUILD_ID="OLR-032";OLR_032_REVISION="OLR_032_CONTINUOUS_CALIBRATION_INGESTION_CYCLE_V1"
@dataclass(frozen=True)
class CalibrationIngestionCycleSummary:
    settled_scanned:int;learned_settlements:int;exact_evidence_matches:int;probability_abstentions:int;candidates:int;admitted:int;duplicate_records:int;ledger_records:int
def run_calibration_ingestion_cycle(root=None,settled_limit=100,evidence_limit=25):
    root=Path(root or Path.cwd()).resolve();batch=assemble_calibration_candidates(root,settled_limit,evidence_limit);path=root/"runtime_state"/"oracle_calibration_ledger.json";ledger=load_calibration_ledger(path);a=d=0
    for c in batch.candidates:
        rec=build_durable_calibration_record(c.calibration_record,c.source_observation_id,c.settlement_hash);ledger,added=admit_calibration_record(ledger,rec)
        if added:a+=1
        else:d+=1
    save_calibration_ledger(path,ledger)
    return CalibrationIngestionCycleSummary(batch.settled_scanned,batch.learned_settlements,batch.exact_evidence_matches,batch.probability_abstentions,len(batch.candidates),a,d,len(ledger))
def verify_olr_032_continuous_calibration_ingestion_cycle():return CalibrationIngestionCycleSummary(0,0,0,0,0,0,0,0).ledger_records==0
