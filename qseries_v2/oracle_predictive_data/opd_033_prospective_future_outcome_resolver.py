
from pathlib import Path
import hashlib,json
REQ=("state_id","resolution_epoch","future_return","mfe","mae","hit_plus_05","hit_minus_05","hit_plus_10","hit_minus_10")
def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def resolve(outcome,root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";states=rt/"opd_032_prospective_state_ledger.jsonl";dst=rt/"opd_033_prospective_outcome_ledger.jsonl"
    if any(k not in outcome for k in REQ):raise ValueError("MISSING_REQUIRED_OUTCOME_FIELD")
    found=None
    if states.exists():
        with states.open(encoding="utf-8") as f:
            for line in f:
                x=json.loads(line)
                if x["state_id"]==outcome["state_id"]:found=x;break
    if found is None:raise ValueError("UNKNOWN_STATE_ID")
    if float(outcome["resolution_epoch"]) < found["observed_epoch"]+found["horizon_seconds"]:raise ValueError("NON_FUTURE_RESOLUTION_REJECTED")
    row={k:outcome[k] for k in REQ};row["ticker"]=found["ticker"];row["horizon_seconds"]=found["horizon_seconds"];row["matched_family_ids"]=found["matched_family_ids"];row["strictly_future"]=True
    seen=set()
    if dst.exists():
        with dst.open(encoding="utf-8") as f:
            for line in f:
                try:seen.add(json.loads(line)["state_id"])
                except:pass
    if row["state_id"] not in seen:
        with dst.open("a",encoding="utf-8") as f:f.write(_canon(row)+"\n")
    return row
def summary(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";dst=rt/"opd_033_prospective_outcome_ledger.jsonl";rows=[]
    if dst.exists():
        with dst.open(encoding="utf-8") as f:rows=[json.loads(x) for x in f if x.strip()]
    s={"schema_version":"OPD-033","resolved_states":len(rows),"resolved_trigger_states":sum(bool(x["matched_family_ids"]) for x in rows),
       "all_strictly_future":all(x["strictly_future"] for x in rows),"execution_authority":False}
    out=rt/"opd_033_prospective_future_outcome_resolver.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
