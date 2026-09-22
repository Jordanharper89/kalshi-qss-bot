from __future__ import annotations
import json,re

TERMS=("attribute_forward_outcomes","price_usd","observed_at","payload","pools",
       "reserve_ratio_change_from_birth","prospective_horizon_schedule","signal_relative_horizon_schedule")

def audit(root):
 files=[]
 roots=[
  root/"qseries_v2/oracle_adapters/independent",
  root/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance",
 ]
 for base in roots:
  if not base.exists():continue
  for p in base.rglob("*.py"):
   s=p.read_text(encoding="utf-8",errors="ignore")
   hits=[t for t in TERMS if t in s]
   if hits:
    files.append({"path":str(p.relative_to(root)).replace("\\","/"),
      "hits":hits,"line_count":len(s.splitlines())})
 runtime=[]
 rb=root/"runtime_state"
 if rb.exists():
  for p in rb.rglob("*.json"):
   try:
    s=p.read_text(encoding="utf-8",errors="ignore")
   except Exception:
    continue
   hits=[t for t in ("price_usd","observed_at","pools","signature","pair_address","horizon_seconds") if t in s]
   if hits:
    runtime.append({"path":str(p.relative_to(root)).replace("\\","/"),
      "hits":hits,"bytes":p.stat().st_size})
 return {"revision":"SULS_096","code_candidates":files,"runtime_candidates":runtime,
  "code_candidate_count":len(files),"runtime_candidate_count":len(runtime),
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/prospective_outcome_source_contract_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
