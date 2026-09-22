from __future__ import annotations
import json
from pathlib import Path

def _load(root,name):
 return json.loads((Path(root)/name).read_text(encoding="utf-8"))

def run(root):
 c=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_executable_entry_exit_contract.json")
 n=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_friction_normalized_rows.json")
 b=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_executable_entry_exit_baseline.json")
 return {"revision":"USLS_122","phase":7,
  "contract_ready":c.get("phase")==7,
  "family_count":len(n.get("family_row_counts",{})),
  "normalized_row_count":n.get("row_count",0),
  "executable_ready_count":b.get("ready_count",0),
  "incomplete_count":b.get("incomplete_count",0),
  "phase7_status":"IN_PROGRESS",
  "phase7_physically_certified":False,
  "remaining_required_capability":"PHYSICAL_FEE_LIQUIDITY_SLIPPAGE_LATENCY_ENRICHMENT_THEN_NET_EXECUTABLE_RETURN",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
