from __future__ import annotations
import json,math
from pathlib import Path
FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"
OOS="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/prospective_setup_feature_join.json"
BLOCK={"freeze_hash","freeze_unix","observed_unix","later_observed_unix","trade_signature","later_trade_signature",
       "market_address","input_asset","output_asset","last_price","entry_reference_price","later_price_in_frozen_orientation",
       "gross_forward_return","execution_authority","read_only","profitability_claimed"}

def _load(p):
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}

def _safe(v):
 if isinstance(v,bool):return int(v)
 if isinstance(v,(int,float)) and math.isfinite(float(v)):return float(v)
 if isinstance(v,str) and len(v)<=64:return v
 return None

def build(root):
 root=Path(root);fz=_load(root/FREEZE);oo=_load(root/OOS)
 idx={x.get("freeze_hash"):x for x in fz.get("frozen_setups",[]) if x.get("freeze_hash")}
 rows=[]
 for c in oo.get("cases",[]):
  h=c.get("freeze_hash");s=idx.get(h)
  if not s or not isinstance(c.get("gross_forward_return"),(int,float)):continue
  feat={}
  for k,v in s.items():
   if k in BLOCK:continue
   q=_safe(v)
   if q is not None:feat[k]=q
  rows.append({"freeze_hash":h,"family":c.get("family") or s.get("family"),
   "freeze_unix":s.get("freeze_unix"),"gross_forward_return":float(c["gross_forward_return"]),
   "pre_outcome_features":feat,"feature_count":len(feat),"execution_authority":False})
 fam={}
 for x in rows:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"SSR_021","joined_case_count":len(rows),"family_counts":fam,"rows":rows,
  "feature_semantics":"ONLY_FIELDS_FROZEN_BEFORE_FORWARD_OUTCOME; OUTCOME_AND_IDENTITY_FIELDS_EXCLUDED",
  "future_leakage":"FORBIDDEN","profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
