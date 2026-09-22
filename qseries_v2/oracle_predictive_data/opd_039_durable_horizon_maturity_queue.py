from pathlib import Path
import hashlib,json,time

def rebuild(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";src=rt/"opd_032_prospective_state_ledger.jsonl";done=rt/"opd_033_prospective_outcome_ledger.jsonl";dst=rt/"opd_039_maturity_queue.json"
    resolved=set()
    if done.exists():
        with done.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():resolved.add(json.loads(line)["state_id"])
    pending=[]
    if src.exists():
        with src.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():continue
                x=json.loads(line)
                if x["state_id"] in resolved:continue
                pending.append({"state_id":x["state_id"],"anchor_id":x.get("anchor_id"),"ticker":x["ticker"],
                                "observed_epoch":x["observed_epoch"],"horizon_seconds":x["horizon_seconds"],
                                "maturity_epoch":float(x["observed_epoch"])+int(x["horizon_seconds"]),
                                "anchor_price":x.get("anchor_price"),"matched_family_ids":x["matched_family_ids"],
                                "anchor_sequence_boundary":x.get("anchor_sequence_boundary"),
                                "anchor_sequence_basis":x.get("anchor_sequence_basis")})
    pending.sort(key=lambda x:(x["maturity_epoch"],x["state_id"]));dst.write_text(json.dumps(pending,indent=2,sort_keys=True))
    now=time.time();s={"schema_version":"OPD-039","pending":len(pending),"mature_now":sum(x["maturity_epoch"]<=now for x in pending),
       "queue_hash":hashlib.sha256(dst.read_bytes()).hexdigest(),"restart_rebuildable":True,"duplicate_resolution_prevented":True,"execution_authority":False}
    out=rt/"opd_039_durable_horizon_maturity_queue.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out

def mature(root=None,now=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";p=rt/"opd_039_maturity_queue.json"
    rows=json.loads(p.read_text()) if p.exists() else [];t=float(now if now is not None else time.time());return [x for x in rows if x["maturity_epoch"]<=t]
