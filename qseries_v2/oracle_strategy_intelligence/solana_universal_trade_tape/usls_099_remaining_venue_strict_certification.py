from __future__ import annotations
import json
from pathlib import Path
REQ={"MOONIT":58,"BOOP_FUN":50,"HEAVEN":59}
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 u=json.loads((b/"remaining_venue_universal_trade_rows.json").read_text(encoding="utf-8"))
 ok=u["venue_counts"]==REQ and u["exact_trade_count"]==sum(REQ.values())
 return {"revision":"USLS_099","strict_remaining_venue_certified":ok,
  "venue_counts":u["venue_counts"],"exact_trade_count":u["exact_trade_count"],
  "phase4_status":"IN_PROGRESS","next_boundary":"PUMPSWAP_048C_SEMANTIC_REPAIR_AND_PHASE4_FINAL_CLOSURE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_strict_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
