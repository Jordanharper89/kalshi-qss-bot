from __future__ import annotations
import json
from pathlib import Path
def append(root):
 src=json.loads((root/"runtime_state/solana_opportunities/learning/real_feature_outcome_cases.json").read_text(encoding="utf-8"))
 cert=json.loads((root/"runtime_state/solana_opportunities/learning/no_future_leakage_certification.json").read_text(encoding="utf-8"))
 if not cert.get("no_future_leakage_certified"):raise RuntimeError("NO_FUTURE_LEAKAGE_CERTIFICATION_REQUIRED")
 p=root/"runtime_state/solana_opportunities/learning/empirical_cases.jsonl";p.parent.mkdir(parents=True,exist_ok=True)
 existing={}
 if p.is_file():
  for line in p.read_text(encoding="utf-8").splitlines():
   if not line.strip():continue
   x=json.loads(line);existing[x["experience_id"]]=x
 before=len(existing)
 for c in src.get("cases",[]):existing[c["experience_id"]]=c
 rows=sorted(existing.values(),key=lambda x:(x["feature_observed_at"],x["experience_id"]))
 p.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows),encoding="utf-8")
 return {"revision":"OSI_070","before":before,"after":len(rows),"appended":len(rows)-before,
  "deduplicated":len(rows)==len({x["experience_id"] for x in rows}),"execution_authority":False}
