from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
def _dt(s):return datetime.fromisoformat(str(s).replace("Z","+00:00"))
def certify(root):
 d=json.loads((root/"runtime_state/solana_opportunities/learning/real_feature_outcome_cases.json").read_text(encoding="utf-8"))
 rows=[]
 for c in d.get("cases",[]):
  fa=_dt(c["feature_observed_at"]);oa=_dt(c["outcome_at"])
  rows.append({"experience_id":c["experience_id"],"horizon_seconds":c["horizon_seconds"],
   "feature_before_outcome":fa<oa,"elapsed_seconds":(oa-fa).total_seconds(),"verified":c["verified"]})
 passed=bool(rows) and all(x["feature_before_outcome"] and x["verified"] and x["elapsed_seconds"]>=x["horizon_seconds"] for x in rows)
 return {"revision":"OSI_069","rows":rows,"case_count":len(rows),"no_future_leakage_certified":passed,
  "execution_authority":False,"read_only":True}
def write(root):
 d=certify(root);p=root/"runtime_state/solana_opportunities/learning/no_future_leakage_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
