from __future__ import annotations
import json
from pathlib import Path
TABLE_TERMS=("oracle","observation","canonical","history","event","source")
COLUMN_TERMS=("canonical_observation_json","observation_type","source_id","observed_at","jsonb","payload","data")
def classify(root:Path)->dict:
 p=root/"runtime_state/solana_opportunities/postgresql_schema_profile.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 out=[]
 for t in d.get("tables",[]):
  table=t["table"];cols=t["columns"]
  names=[str(x["column"]).lower() for x in cols];types=[str(x["type"]).lower() for x in cols]
  text=(table+" "+" ".join(names)+" "+" ".join(types)).lower()
  score=sum(2 for k in TABLE_TERMS if k in table.lower())+sum(1 for k in COLUMN_TERMS if k in text)
  has_time="observed_at" in names
  has_json=any(x["column"]=="canonical_observation_json" and x["type"]=="jsonb" for x in cols)
  if score>0:out.append({"table":table,"score":score,"has_observed_at":has_time,"has_canonical_json":has_json,"columns":cols})
 out.sort(key=lambda x:(not x["has_canonical_json"],not x["has_observed_at"],-x["score"],x["table"]))
 return {"revision":"OSI_041B","candidates":out,"candidate_count":len(out),"execution_authority":False,"read_only":True}
def write(root:Path)->Path:
 d=classify(root);p=root/"runtime_state/solana_opportunities/solana_postgresql_tables.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
