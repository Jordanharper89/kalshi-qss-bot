from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase7_live_friction_normalized.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"))
 fam=d.get("family_support",{})
 observed=sorted(fam)
 liquidity_ready=sorted(f for f,v in fam.items() if v.get("liquidity_reference",0)>0)
 latency_ready=sorted(f for f,v in fam.items() if v.get("latency",0)>0)
 fee_ready=sorted(f for f,v in fam.items() if v.get("network_fee",0)>0)
 return {"revision":"USLS_147","phase":7,
  "live_observed_family_count":len(observed),"live_observed_families":observed,
  "latency_ready_families":latency_ready,"network_fee_ready_families":fee_ready,
  "certified_liquidity_role_ready_families":liquidity_ready,
  "phase7_status":"IN_PROGRESS","phase7_physically_certified":False,
  "remaining_required_capability":
   "PROTOCOL_FEE_AND_POOL_LIQUIDITY_ROLE_RESOLUTION_FOR_LIVE_VENUES_PLUS_LIVE_COHORTS_FOR_UNOBSERVED_DAMM_MOONIT_BOOP_HEAVEN",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_live_friction_coverage_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
