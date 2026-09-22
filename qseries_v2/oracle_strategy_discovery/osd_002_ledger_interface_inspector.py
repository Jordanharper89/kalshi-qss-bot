from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / "runtime/predictive_data/opd_full_evidence_live_prediction_ledger.jsonl"
OUTC = ROOT / "runtime/predictive_data/opd_full_evidence_live_outcome_ledger.jsonl"

def first_rows(path, n=3):
    out=[]
    with path.open("r",encoding="utf-8") as f:
        for line in f:
            try:
                x=json.loads(line)
                if isinstance(x,dict):
                    out.append(x)
                    if len(out)>=n: break
            except Exception: pass
    return out

def show(name, rows):
    print("="*100)
    print(name)
    for i,r in enumerate(rows,1):
        print("[ROW]",i)
        print("[TOP KEYS]",sorted(r.keys()))
        for k,v in r.items():
            if isinstance(v,dict):
                print("[DICT]",k,"KEYS=",sorted(v.keys()))
        for k in ("prediction_id","prediction_record_id","prospective_prediction_id","state_id",
                  "anchor_sequence","anchor_sequence_number","sequence_number","prediction_epoch",
                  "frozen_epoch","created_epoch","anchor_epoch","observed_epoch",
                  "ticker","market_ticker","future_return","realized_return","yes_price_return"):
            if k in r: print("[FIELD]",k,"=",r.get(k))

show("PREDICTION LEDGER", first_rows(PRED))
show("OUTCOME LEDGER", first_rows(OUTC))
print("="*100)
print("[RESULT] OSD_002_LEDGER_INTERFACE_INSPECTION_COMPLETE")
