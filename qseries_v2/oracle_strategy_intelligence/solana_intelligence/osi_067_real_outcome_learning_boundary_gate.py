from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 outcome=root/"runtime_state/solana_opportunities/outcomes/verified_forward_outcomes.json"
 anchor=root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json"
 present={"verified_outcomes":outcome.is_file(),"fresh_anchor":anchor.is_file()}
 verified=0;horizons=[]
 if outcome.is_file():
  d=json.loads(outcome.read_text(encoding="utf-8"));verified=int(d.get("verified_outcomes",0));horizons=d.get("resolved_horizons",[])
 ready=all(present.values()) and verified>0
 return {"components_present":present,"verified_outcomes":verified,"resolved_horizons":horizons,
  "real_outcome_learning_boundary_ready":ready,"execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/real_outcome_learning_boundary.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
