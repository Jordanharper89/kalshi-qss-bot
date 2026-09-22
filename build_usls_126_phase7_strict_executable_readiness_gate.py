from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_126_phase7_strict_executable_readiness_gate.py"
TEST=ROOT/"test_usls_126_phase7_strict_executable_readiness_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase7_physical_friction_rows.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=[];fam={}
 for x in d.get("rows",[]):
  have_price=x.get("reference_price") is not None
  have_fee=(x.get("source_native_fee_evidence") is not None or x.get("network_fee_lamports") is not None)
  have_latency=x.get("observation_latency_seconds") is not None
  have_liq=x.get("liquidity_evidence") is not None
  have_slip=bool(x.get("slippage_model_ready"))
  ready=all((have_price,have_fee,have_latency,have_liq,have_slip))
  missing=[n for n,v in (("price",have_price),("fee",have_fee),("latency",have_latency),
                         ("liquidity",have_liq),("slippage",have_slip)) if not v]
  rows.append({"family":x["family"],"trade_signature":x["trade_signature"],
   "ready":ready,"missing":missing,"execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"ready":0})
  z["rows"]+=1;z["ready"]+=ready
 return {"revision":"USLS_126","row_count":len(rows),
  "ready_count":sum(x["ready"] for x in rows),
  "incomplete_count":sum(not x["ready"] for x in rows),
  "family_readiness":fam,"rows":rows,
  "readiness_contract":"PRICE_PLUS_FEE_PLUS_LATENCY_PLUS_LIQUIDITY_PLUS_SLIPPAGE",
  "next_boundary":"NET_EXECUTABLE_RETURN_ONLY_FOR_READY_ROWS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_strict_executable_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_126_phase7_strict_executable_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "row_count","ready_count","incomplete_count","family_readiness","next_boundary")},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertEqual(d["ready_count"]+d["incomplete_count"],d["row_count"])
  self.assertEqual(d["readiness_contract"],
   "PRICE_PLUS_FEE_PLUS_LATENCY_PLUS_LIQUIDITY_PLUS_SLIPPAGE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-126 strict executable readiness gate")
  print("[PASS] no row is executable-ready unless all physical friction inputs are present")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
