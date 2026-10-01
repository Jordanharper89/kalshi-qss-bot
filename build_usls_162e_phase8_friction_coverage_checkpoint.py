from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162e_phase8_friction_coverage_checkpoint.py"
TEST=ROOT/"test_usls_162e_phase8_friction_coverage_checkpoint.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
LED="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
FRI="runtime_state/solana_opportunities/solana_scanner/phase8_physical_friction_linkage.json"
CHK="runtime_state/solana_opportunities/solana_scanner/phase8_updated_learning_coverage_checkpoint.json"
def run(root):
 root=Path(root);led=json.loads((root/LED).read_text(encoding="utf-8"));fri=json.loads((root/FRI).read_text(encoding="utf-8"));chk=json.loads((root/CHK).read_text(encoding="utf-8"))
 fam={}
 for x in led.get("cases",[]):fam[x["family"]]=fam.get(x["family"],0)+1
 supported=set(fri.get("friction_supported_families") or [])
 rows=[{"family":f,"prospective_oos_cases":n,"physical_friction_supported":f in supported,
        "gap":None if f in supported else "NO_MATCHING_PHASE7_STRICT_EXECUTABLE_FRICTION"} for f,n in sorted(fam.items())]
 return {"revision":"USLS_162E","prospective_oos_case_count":len(led.get("cases",[])),
  "phase8_family_ready_count":chk.get("family_ready_count"),"friction_supported_case_count":fri.get("friction_supported_case_count"),
  "families":rows,"net_expectancy_ready":bool(fri.get("friction_supported_case_count")),
  "next_boundary":"CLOSE_PUMP_FUN_DIRECT_DECODER_AND_CAPTURE_PUMPSWAP_OOS_OR_EXPAND_PHASE7_FRICTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_friction_coverage_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162e_phase8_friction_coverage_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["prospective_oos_case_count"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162E Phase 8 friction coverage checkpoint")
  print("[NEXT]",d["next_boundary"])
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
