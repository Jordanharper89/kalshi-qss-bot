import json
from pathlib import Path
from .slop_061_canonical_prospective_learning_evidence import learning_evidence
from .slop_062_native_ocl_prospective_outcome_bridge import build_slop_learning_input

def _path(root): return Path(root)/"runtime_state/solana_live_opportunity/slop_063_learning_admissions.json"

def candidate_inputs(root=None):
 root=Path(root or Path.cwd()); chosen={}
 for e in sorted(learning_evidence(root),key=lambda x:(x["frozen_at"],x["prediction_id"])):
  chosen.setdefault(e["token_address"],e)
 out=[]
 for seq,e in enumerate(chosen.values(),1):
  oo,ev,ri=build_slop_learning_input(seq,e)
  out.append((e,oo,ev,ri))
 return out

def admit(root=None):
 root=Path(root or Path.cwd()); p=_path(root)
 old=json.loads(p.read_text()) if p.exists() else []
 seen={x["event_id"] for x in old}; added=[]
 for e,oo,ev,ri in candidate_inputs(root):
  if ev.event_id in seen: continue
  added.append({"event_id":ev.event_id,"token_address":e["token_address"],
   "prediction_id":e["prediction_id"],"evidence_hash":e["evidence_hash"],
   "input_hash":ri.input_hash,"status":"ADMITTED"})
  seen.add(ev.event_id)
 if added:
  p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(json.dumps(old+added,indent=2,sort_keys=True),encoding="utf-8")
 return added
