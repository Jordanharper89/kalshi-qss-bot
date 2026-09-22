from __future__ import annotations
import json
from pathlib import Path

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 r=json.loads((b/"pumpswap_048c_repaired_trades.json").read_text(encoding="utf-8"))
 ok=(r["exact_trade_count"]==117 and all(r["repairs"].values()) and r["execution_authority"] is False)
 matrix={
  "PUMP_SWAP":{"program_id":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA","exact_trade_rows":r["exact_trade_count"],
   "semantic_repair":"048C","identity_revision":"USLS_047C","status":"CERTIFIED" if ok else "BLOCKED"}}
 return {"revision":"USLS_102","matrix_revision":"049C","pumpswap_certified":ok,"matrix":matrix,
  "phase4_status":"IN_PROGRESS","next_boundary":"PHASE4_STRICT_FULL_VENUE_CLOSURE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_049c_certification_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
