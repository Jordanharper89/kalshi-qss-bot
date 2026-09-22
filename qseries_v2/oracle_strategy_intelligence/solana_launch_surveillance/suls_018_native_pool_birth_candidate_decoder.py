from __future__ import annotations
import json
from pathlib import Path

BIRTH_PATTERNS=(
 "initialize_pool","initialize pool","initialize2","create_pool","create pool",
 "initialize_pool_v2","initializepool","pool initialize","pool created"
)

def decode(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/live_native_transaction_program_scan.json"
 d=json.loads(src.read_text(encoding="utf-8"));out=[]
 for tx in d.get("rows",[]):
  logs=[str(x) for x in tx.get("logs") or ()]
  low="\n".join(logs).lower()
  hits=sorted({p for p in BIRTH_PATTERNS if p in low})
  if not hits:continue
  out.append({"slot":tx.get("slot"),"signature":tx.get("signature"),"block_time":tx.get("block_time"),
   "program_ids":tx.get("program_ids") or [],"birth_log_patterns":hits,
   "logs":logs,"decoder_state":"POOL_BIRTH_CANDIDATE","execution_authority":False})
 return {"revision":"SULS_018","transaction_count":d.get("transaction_count",0),
  "candidate_count":len(out),"candidates":out,"execution_authority":False,"read_only":True,
  "scope":"LOG_SEMANTIC_CANDIDATES_ONLY_NOT_YET_VERIFIED_POOL_BIRTHS"}

def write(root):
 d=decode(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_pool_birth_candidates.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
