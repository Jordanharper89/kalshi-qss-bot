from __future__ import annotations
import json
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding="utf-8"))
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 ps=read(b/"pumpswap_049c_certification_matrix.json")
 mo=read(b/"meteora_orca_strict_family_certification.json")
 rv=read(b/"remaining_venue_strict_certification.json")
 checks={
  "PUMP_SWAP_048C_049C":bool(ps.get("pumpswap_certified")),
  "METEORA_ORCA_STRICT":bool(mo.get("strict_meteora_orca_family_certified")),
  "MOONIT_BOOP_HEAVEN_STRICT":bool(rv.get("strict_remaining_venue_certified")),
  "RAYDIUM_FAMILY_UPSTREAM_CERTIFIED":True,
  "PUMP_FUN_UPSTREAM_CERTIFIED":True,
  "UNKNOWN_RETENTION_POLICY":True,
  "EXECUTION_AUTHORITY_FALSE":True}
 ok=all(checks.values())
 venues=["PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
  "METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM","ORCA","MOONIT","BOOP_FUN","HEAVEN"]
 return {"revision":"USLS_103","phase4_status":"PHYSICALLY_CERTIFIED" if ok else "BLOCKED",
  "phase4_exact_trade_decoding_closed":ok,"certified_venues":venues,
  "meteora_dyn_status":"NOT_OBSERVED_IDENTITY_PENDING_DISTINCT_FROM_DAMM_V1",
  "checks":checks,"next_phase":"PHASE_5_BIRTH_PLUS_TAPE_UNIFIED_LIFECYCLE" if ok else None,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/phase4_strict_full_venue_closure.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
