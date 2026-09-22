from __future__ import annotations
import json,re
from pathlib import Path

TERMS=("initialize","create","launch","migration","migrate","pool","mint","bonding","curve","liquidity")

def correlate(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 ev=json.loads((base/"live_multifamily_transactions.json").read_text(encoding="utf-8"))
 ix=json.loads((base/"live_program_instruction_evidence.json").read_text(encoding="utf-8"))
 tx_by_sig={r.get("signature"):r for r in ev.get("rows") or []}
 out=[]
 for row in ix.get("rows") or []:
  tx=(tx_by_sig.get(row["signature"]) or {}).get("raw_transaction") or {}
  logs=((tx.get("meta") or {}).get("logMessages") or [])
  hits=[]
  for line in logs:
   low=str(line).lower()
   if row["program_id"].lower() in low or any(t in low for t in TERMS):
    hits.append(str(line))
  out.append({**row,"birth_log_hits":hits[:80],
   "birth_term_hits":sorted({t for t in TERMS if any(t in str(z).lower() for z in logs)}),
   "candidate_birth_evidence":bool(hits)})
 fam={}
 for r in out:
  f=r["matched_family"];s=fam.setdefault(f,{"instructions":0,"with_birth_evidence":0})
  s["instructions"]+=1;s["with_birth_evidence"]+=int(r["candidate_birth_evidence"])
 return {"revision":"USLS_016","family_summary":fam,"rows":out,
  "execution_authority":False,"read_only":True}

def write(root):
 d=correlate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/birth_log_instruction_correlation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
