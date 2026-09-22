from __future__ import annotations
import json
from pathlib import Path

REQ={"METEORA_DBC":17,"METEORA_DAMM_V2":3,"METEORA_DLMM":1,
     "METEORA_DAMM_V1":19,"ORCA":2}

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 u=json.loads((b/"meteora_orca_universal_trade_rows.json").read_text(encoding="utf-8"))
 counts=u["venue_counts"]
 ok=all(int(counts.get(k,0))>=v for k,v in REQ.items())
 return {"revision":"USLS_085",
  "strict_meteora_orca_family_certified":ok,
  "exact_trade_count":u["exact_trade_count"],"venue_counts":counts,
  "orientation_policy":u["orientation_policy"],
  "phase4_status":"IN_PROGRESS",
  "next_boundary":"MOONIT_BOOP_HEAVEN_SHARED_DECODER_DISCOVERY",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_strict_family_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
