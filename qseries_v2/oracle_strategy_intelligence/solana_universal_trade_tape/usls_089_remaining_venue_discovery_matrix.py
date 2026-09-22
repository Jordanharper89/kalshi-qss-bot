from __future__ import annotations
import json
from pathlib import Path

VENUES=("MOONIT","BOOP_FUN","HEAVEN")

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 h=json.loads((b/"remaining_venue_live_transactions.json").read_text(encoding="utf-8"))
 f=json.loads((b/"remaining_venue_instruction_fingerprints.json").read_text(encoding="utf-8"))
 matrix={}
 for v in VENUES:
  selected=int(h["selected_counts"].get(v,0))
  hydrated=int(h["hydrated_counts"].get(v,0))
  fps=sum(1 for x in f["rows"] if x["venue"]==v)
  status=("PHYSICAL_ACTIVITY_AND_FINGERPRINTS_READY_FOR_SEMANTIC_DECODER"
   if hydrated and fps else
   ("HYDRATED_NO_PROGRAM_DATA" if hydrated else "NO_HYDRATED_ACTIVITY"))
  matrix[v]={"selected_transactions":selected,
   "hydrated_transactions":hydrated,
   "instruction_fingerprints":fps,"status":status}
 return {"revision":"USLS_089","matrix":matrix,
  "phase4_status":"IN_PROGRESS",
  "next_boundary":"SOURCE_BACKED_TRADE_SEMANTICS_FOR_MOONIT_BOOP_HEAVEN",
  "profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_discovery_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
