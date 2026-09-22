from __future__ import annotations
import json

FILES=(
 "oad312_314_shared_contract.json",
 "oad314_callable_interface.json",
 "oad314_case_record_contract.json",
 "oad314_forward_outcome_lineage.json",
 "oad314_runtime_callables.json",
 "temporal_record_producer_lineage.json",
 "temporal_runtime_callables.json",
)

def extract(root):
 base=root/"runtime_state/solana_opportunities"
 out={}
 for name in FILES:
  p=base/name
  if not p.exists():
   out[name]={"exists":False}
   continue
  try:
   d=json.loads(p.read_text(encoding="utf-8"))
  except Exception as e:
   out[name]={"exists":True,"error":repr(e)}
   continue
  out[name]={"exists":True,"keys":sorted(d.keys()),"data":d}
 return {"revision":"SULS_097","contracts":out,
  "execution_authority":False,"read_only":True}

def write(root):
 d=extract(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/oad314_exact_temporal_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
