from __future__ import annotations
import json
from pathlib import Path

SYSTEM="11111111111111111111111111111111"

def classify(root):
 root=Path(root)
 reg=json.loads((root/"runtime_state/solana_opportunities/universal_launch_scanner/family_registry.json").read_text(encoding="utf-8"))
 shapes=json.loads((root/"runtime_state/solana_opportunities/universal_launch_scanner/universal_transaction_shapes.json").read_text(encoding="utf-8"))
 id_to_family={}
 for fam,r in reg["families"].items():
  for pid in r.get("program_ids") or []:id_to_family[pid]=fam
 out=[]
 for r in shapes["rows"]:
  logs=" ".join(r.get("logs") or []).lower()
  parsed=[str(x.get("parsed_type") or "").lower() for x in r.get("instructions") or []]
  known=sorted({id_to_family[p] for p in r.get("program_ids") or [] if p in id_to_family})
  mints={x.get("mint") for x in r.get("token_balances") or [] if x.get("mint")}
  create_signal=("create pool" in logs or "initializepool" in logs or "initialize pool" in logs
   or "migration" in logs or "initializeaccount" in logs)
  token_signal=len(mints)>=2 or "transferchecked" in parsed or "initializemint2" in parsed
  structural_score=int(create_signal)+int(token_signal)+int(len(r.get("account_keys") or [])>=8)+int(len(r.get("instructions") or [])>=1)
  state=("CONFIRMED_POOL_BIRTH_CANDIDATE" if structural_score>=3 and create_signal
         else "PROBABLE_POOL_BIRTH_CANDIDATE" if structural_score>=2
         else "UNRESOLVED_EVENT")
  family=known[0] if len(known)==1 else ("MULTI_PROGRAM" if len(known)>1 else "UNKNOWN_PROGRAM")
  out.append({"signature":r.get("signature"),"slot":r.get("slot"),"observed_unix":r.get("observed_unix"),
   "family":family,"known_families":known,"candidate_state":state,
   "structural_score":structural_score,"create_signal":create_signal,"token_signal":token_signal,
   "program_ids":r.get("program_ids") or [],"execution_authority":False})
 return {"revision":"USLS_003","event_count":len(out),
  "retained_count":len(out),"dropped_count":0,
  "candidate_count":sum(1 for x in out if x["candidate_state"]!="UNRESOLVED_EVENT"),
  "unknown_retained_count":sum(1 for x in out if x["family"]=="UNKNOWN_PROGRAM"),
  "events":out,"execution_authority":False,"read_only":True}

def write(root):
 d=classify(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/structural_birth_candidates.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
