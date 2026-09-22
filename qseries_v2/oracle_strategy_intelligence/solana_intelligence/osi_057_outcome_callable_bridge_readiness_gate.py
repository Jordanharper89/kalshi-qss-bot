from __future__ import annotations
import json
from pathlib import Path

CASE_REQUIRED={
 "snapshot_at","horizon_seconds","evidence_observation_ids",
 "pair_address","experience_id","token_address"
}
RECORD_REQUIRED={"observed_at","observation_id"}

def gate(root):
 files={
  "oad314_contract":root/"runtime_state/solana_opportunities/oad314_case_record_contract.json",
  "oad314_callables":root/"runtime_state/solana_opportunities/oad314_runtime_callables.json",
  "oad312_interface":root/"runtime_state/solana_opportunities/oad312_temporal_history_interface.json",
 }
 present={k:p.is_file() for k,p in files.items()}

 case_attrs=set();record_attrs=set();price_attrs=set();price_keys=set();callables=[]
 if files["oad314_contract"].is_file():
  d=json.loads(files["oad314_contract"].read_text(encoding="utf-8"))
  fn=d.get("functions",{})
  a=fn.get("attribute_forward_outcomes",{})
  p=fn.get("_price_for_pair",{})
  case_attrs={x["attribute"] for x in a.get("attributes",[]) if x.get("owner")=="c"}
  record_attrs={x["attribute"] for x in a.get("attributes",[]) if x.get("owner")=="r"}
  price_attrs={x["attribute"] for x in p.get("attributes",[]) if x.get("owner")=="record"}
  price_keys={x["key"] for x in p.get("dict_keys",[])}

 if files["oad314_callables"].is_file():
  d=json.loads(files["oad314_callables"].read_text(encoding="utf-8"))
  callables=d.get("callables",[])

 callable_names={x.get("name") for x in callables}
 ready=(
  all(present.values())
  and CASE_REQUIRED.issubset(case_attrs)
  and RECORD_REQUIRED.issubset(record_attrs)
  and "payload" in price_attrs
  and {"pools","pair_address","price_usd"}.issubset(price_keys)
  and "attribute_forward_outcomes" in callable_names
 )

 return {
  "components_present":present,
  "case_attributes":sorted(case_attrs),
  "record_attributes":sorted(record_attrs),
  "price_record_attributes":sorted(price_attrs),
  "price_dict_keys":sorted(price_keys),
  "callable_names":sorted(x for x in callable_names if x),
  "callable_bridge_ready":ready,
  "execution_authority":False,
  "read_only":True,
 }

def write(root):
 d=gate(root)
 p=root/"runtime_state/solana_opportunities/outcome_callable_bridge_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
