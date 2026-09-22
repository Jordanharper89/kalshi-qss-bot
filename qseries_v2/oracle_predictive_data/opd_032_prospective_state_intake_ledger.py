from pathlib import Path
import hashlib,json
FORBIDDEN={"future_target","future_return","mfe","mae","hit_plus_05","hit_minus_05","hit_plus_10","hit_minus_10","resolution_epoch"}

def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def _paths(root):
    rt=Path(root)/"runtime"/"predictive_data";return rt,rt/"opd_032_prospective_state_ledger.jsonl"

def observe(snapshot,root=None):
    root=Path(root or Path.cwd());rt,ledger=_paths(root);freeze=json.loads((rt/"opd_031_prospective_candidate_freeze.json").read_text())
    if FORBIDDEN.intersection(snapshot):raise ValueError("POST_T_OR_OUTCOME_FIELD_REJECTED")
    req=("anchor_id","ticker","observed_epoch","horizon_seconds","tokens")
    if any(k not in snapshot for k in req):raise ValueError("MISSING_REQUIRED_STATE_FIELD")
    if float(snapshot["observed_epoch"])<=float(freeze["activation_epoch"]):raise ValueError("PRE_FREEZE_STATE_REJECTED")
    toks=set(snapshot["tokens"]);h=int(snapshot["horizon_seconds"]);matches=[]
    for c in freeze["candidates"]:
        if int(c["horizon_seconds"])==h and all(t in toks for t in c["formula"]):matches.append(c["family_id"])
    state_id=hashlib.sha256(_canon([snapshot["anchor_id"],snapshot["ticker"],snapshot["observed_epoch"],h]).encode()).hexdigest()
    row={"state_id":state_id,"anchor_id":snapshot["anchor_id"],"ticker":snapshot["ticker"],
         "observed_epoch":float(snapshot["observed_epoch"]),"horizon_seconds":h,"tokens":sorted(toks),
         "anchor_price":snapshot.get("anchor_price"),"matched_family_ids":matches,"post_freeze":True,
         "anchor_sequence_boundary":snapshot.get("anchor_sequence_boundary"),
         "anchor_sequence_basis":snapshot.get("anchor_sequence_basis")}
    seen=set()
    if ledger.exists():
        with ledger.open(encoding="utf-8") as f:
            for line in f:
                try:seen.add(json.loads(line)["state_id"])
                except:pass
    if state_id not in seen:
        with ledger.open("a",encoding="utf-8") as f:f.write(_canon(row)+"\n")
    return row

def summary(root=None):
    root=Path(root or Path.cwd());rt,ledger=_paths(root);rows=[]
    if ledger.exists():
        with ledger.open(encoding="utf-8") as f:rows=[json.loads(x) for x in f if x.strip()]
    s={"schema_version":"OPD-032","states":len(rows),"trigger_states":sum(bool(x["matched_family_ids"]) for x in rows),
       "unique_tickers":len({x["ticker"] for x in rows}),"all_post_freeze":all(x["post_freeze"] for x in rows),"execution_authority":False}
    out=rt/"opd_032_prospective_state_intake_ledger.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
