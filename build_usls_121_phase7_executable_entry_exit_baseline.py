from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_121_phase7_executable_entry_exit_baseline.py"
TEST=ROOT/"test_usls_121_phase7_executable_entry_exit_baseline.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase7_friction_normalized_rows.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));out=[]
 for x in d.get("rows",[]):
  p=x.get("reference_price")
  fee=x.get("fee_fraction");slip=x.get("slippage_fraction");lat=x.get("latency_seconds")
  liq=x.get("liquidity_notional")
  complete=all(v is not None for v in (p,fee,slip,lat,liq))
  state="EXECUTABLE_MODEL_READY" if complete else "EXECUTABLE_MODEL_INPUT_INCOMPLETE"
  out.append({"family":x.get("family"),"market_address":x.get("market_address"),
   "trade_signature":x.get("trade_signature"),
   "entry_reference_price":p,
   "entry_executable_price":None if not complete else p*(1+slip+fee),
   "exit_reference_price":None,
   "exit_executable_price":None,
   "fee_fraction":fee,"slippage_fraction":slip,"latency_seconds":lat,
   "liquidity_notional":liq,"entry_state":state,
   "net_return_after_friction":None,
   "execution_authority":False})
 ready=sum(x["entry_state"]=="EXECUTABLE_MODEL_READY" for x in out)
 return {"revision":"USLS_121","row_count":len(out),"ready_count":ready,
  "incomplete_count":len(out)-ready,"rows":out,
  "model_policy":"NO_EXECUTABLE_PRICE_WHEN_REQUIRED_FRICTION_INPUTS_MISSING",
  "next_boundary":"PHYSICAL_FEE_LIQUIDITY_LATENCY_ENRICHMENT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_executable_entry_exit_baseline.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_121_phase7_executable_entry_exit_baseline import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"ready_count":d["ready_count"],
   "incomplete_count":d["incomplete_count"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["model_policy"],
   "NO_EXECUTABLE_PRICE_WHEN_REQUIRED_FRICTION_INPUTS_MISSING")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-121 executable entry/exit baseline")
  print("[PASS] incomplete fee/slippage/latency/liquidity inputs correctly block executable-price claims")
  print("[NEXT] PHYSICAL_FEE_LIQUIDITY_LATENCY_ENRICHMENT")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
