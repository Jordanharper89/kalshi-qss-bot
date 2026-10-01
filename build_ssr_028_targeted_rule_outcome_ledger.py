from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_028_targeted_rule_outcome_ledger.py"
TEST=ROOT/"test_ssr_028_targeted_rule_outcome_ledger.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_027_targeted_rule_freeze_filter import build as targets
OOS="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/targeted_rule_outcomes.json"
def build(root):
 root=Path(root);t=targets(root);d=json.loads((root/OOS).read_text(encoding="utf-8"))
 wanted={x["freeze_hash"] for x in t["rows"]};rows=[]
 for x in d.get("cases",[]):
  if x.get("freeze_hash") in wanted and x.get("family")=="PUMP_SWAP":
   rows.append({"freeze_hash":x.get("freeze_hash"),"market_address":x.get("market_address"),
    "freeze_unix":x.get("freeze_unix"),"later_observed_unix":x.get("later_observed_unix"),
    "gross_forward_return":x.get("gross_forward_return"),"later_trade_signature":x.get("later_trade_signature"),
    "execution_authority":False})
 vals=[float(x["gross_forward_return"]) for x in rows if isinstance(x.get("gross_forward_return"),(int,float))]
 return {"revision":"SSR_028","targeted_case_count":len(vals),
  "mean_gross_return":None if not vals else sum(vals)/len(vals),
  "positive_frequency":None if not vals else sum(v>0 for v in vals)/len(vals),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_028_targeted_rule_outcome_ledger import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_ledger(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"targeted_case_count":d["targeted_case_count"],"mean_gross_return":d["mean_gross_return"],"positive_frequency":d["positive_frequency"]},sort_keys=True))
  self.assertFalse(d["execution_authority"]);print("[PASS] SSR-028 targeted rule outcome ledger")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")