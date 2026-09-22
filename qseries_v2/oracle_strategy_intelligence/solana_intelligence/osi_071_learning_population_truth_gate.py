from __future__ import annotations
import json,collections
from pathlib import Path
def gate(root):
 p=root/"runtime_state/solana_opportunities/learning/empirical_cases.jsonl";rows=[]
 if p.is_file():
  rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
 by_h=collections.Counter(int(x["horizon_seconds"]) for x in rows)
 by_cls=collections.Counter(x["outcome_class"] for x in rows)
 formula_ready=len(rows)>=100 and all(by_h.get(h,0)>=20 for h in (5,15,30,60))
 return {"revision":"OSI_071","sample_size":len(rows),"by_horizon":dict(sorted(by_h.items())),
  "by_class":dict(sorted(by_cls.items())),"population_ingestion_ready":len(rows)>0,
  "formula_discovery_statistically_ready":formula_ready,
  "minimum_formula_sample_target":100,"minimum_per_short_horizon":20,
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/learning/population_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
