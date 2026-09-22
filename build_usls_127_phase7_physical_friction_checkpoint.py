from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_127_phase7_physical_friction_checkpoint.py"
TEST=ROOT/"test_usls_127_phase7_physical_friction_checkpoint.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_127_phase7_physical_friction_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["phase"],7)
  self.assertGreater(d["onchain_family_probe_count"],0)
  self.assertGreater(d["source_native_evidence_rows"],0)
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["phase7_physically_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-127 Phase 7 physical-friction checkpoint")
  print("[PASS] physical friction evidence measured without premature executable-profit claims")
  print("[NEXT]",d["remaining_required_capability"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
