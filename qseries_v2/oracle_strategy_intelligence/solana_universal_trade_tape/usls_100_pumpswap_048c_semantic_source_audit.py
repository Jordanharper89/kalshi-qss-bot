from __future__ import annotations
import json
from pathlib import Path

def load_jsons(base):
 out=[]
 for p in base.rglob("*.json"):
  try:
   d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:
   continue
  out.append((p,d))
 return out

def rows_of(d):
 if isinstance(d,dict):
  for k in ("rows","trades","events"):
   if isinstance(d.get(k),list):return d[k]
 return []

def is_pumpswap_row(x):
 return isinstance(x,dict) and (x.get("venue")=="PUMP_SWAP" or x.get("program_id")=="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")

def build(root):
 base=Path(root)/"runtime_state"
 candidates=[]
 for p,d in load_jsons(base):
  rs=[x for x in rows_of(d) if is_pumpswap_row(x)]
  if rs:
   candidates.append({"path":str(p.relative_to(root)),"row_count":len(rs),"revision":d.get("revision"),
    "exact_like_count":sum(str(x.get("decoder_state","")).startswith("EXACT") for x in rs),
    "sample_keys":sorted(rs[0].keys()) if rs else []})
 candidates.sort(key=lambda x:(x["exact_like_count"],x["row_count"]),reverse=True)
 return {"revision":"USLS_100","candidate_count":len(candidates),"candidates":candidates,
  "required_defects":["FALSE_INSTRUCTION_INDEX_FROM_LOG_INDEX","FALSE_EVENT_TIMESTAMP_AS_BLOCK_TIME","STALE_IDENTITY_REVISION_047B"],
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_source_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
