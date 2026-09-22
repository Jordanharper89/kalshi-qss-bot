from __future__ import annotations
import json
from pathlib import Path

def _load(root,name):
 return json.loads((Path(root)/name).read_text(encoding="utf-8"))

def run(root):
 tx=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_onchain_fee_latency_probe.json")
 src=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_source_native_friction_evidence.json")
 gate=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_strict_executable_readiness.json")
 ready=gate.get("ready_count",0)
 return {"revision":"USLS_127","phase":7,
  "onchain_family_probe_count":tx.get("family_probe_count",0),
  "transaction_readback_count":tx.get("tx_found_count",0),
  "source_native_evidence_rows":src.get("row_count",0),
  "executable_ready_count":ready,
  "incomplete_count":gate.get("incomplete_count",0),
  "phase7_status":"IN_PROGRESS",
  "phase7_physically_certified":False,
  "remaining_required_capability":(
   "BUILD_MISSING_PRE_TRADE_LIQUIDITY_REFERENCE_AND_SLIPPAGE_MODELS_THEN_NET_EXECUTABLE_RETURN"
   if ready==0 else
   "NET_EXECUTABLE_ENTRY_EXIT_RETURN_ON_READY_ROWS_AND_EXPAND_COVERAGE"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_physical_friction_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
