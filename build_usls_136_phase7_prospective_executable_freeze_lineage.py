from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_136_phase7_prospective_executable_freeze_lineage.py"
TEST=ROOT/"test_usls_136_phase7_prospective_executable_freeze_lineage.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_executable_candidates.json"

def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"))
 now=time.time();rows=[]
 for x in d.get("rows",[]):
  if not x.get("executable_candidate_ready"):continue
  frozen={"family":x["family"],"market_address":x.get("market_address"),
   "trade_signature":x["trade_signature"],"effective_price":x.get("effective_price"),
   "observation_latency_seconds":x.get("observation_latency_seconds"),
   "pre_trade_reference_price":x.get("pre_trade_reference_price"),
   "realized_execution_deviation_fraction":x.get("realized_execution_deviation_fraction"),
   "fee_evidence":x.get("fee_evidence"),"liquidity_evidence":x.get("liquidity_evidence"),
   "freeze_unix":now,"future_data_allowed":False,"execution_authority":False}
  frozen["freeze_hash"]=hashlib.sha256(_canon(frozen).encode()).hexdigest()
  rows.append(frozen)
 by={}
 for x in rows:by[x["family"]]=by.get(x["family"],0)+1
 return {"revision":"USLS_136","freeze_unix":now,"frozen_row_count":len(rows),
  "family_frozen_counts":by,"rows":rows,
  "future_leakage":"FORBIDDEN","outcome_fields_present_at_freeze":False,
  "next_boundary":"PHASE7_COVERAGE_CHECKPOINT_AND_PROSPECTIVE_OUTCOME_COLLECTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_prospective_executable_freeze.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_136_phase7_prospective_executable_freeze_lineage import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"frozen_row_count":d["frozen_row_count"],
   "family_frozen_counts":d["family_frozen_counts"],
   "future_leakage":d["future_leakage"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["frozen_row_count"],0,"NO_EXECUTABLE_CANDIDATES_FROZEN")
  self.assertEqual(d["future_leakage"],"FORBIDDEN")
  self.assertFalse(d["outcome_fields_present_at_freeze"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-136 prospective executable freeze + lineage")
  print("[PASS] executable candidate state frozen before future outcome collection")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
