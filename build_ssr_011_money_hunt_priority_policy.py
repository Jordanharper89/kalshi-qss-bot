from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_011_money_hunt_priority.py"
TEST=ROOT/"test_ssr_011_money_hunt_priority_policy.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

FRI="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"

def policy(root):
 root=Path(root);p=root/FRI
 d=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
 fam={}
 for x in d.get("ready_rows") or []:
  f=x.get("family")
  if f:fam[f]=fam.get(f,0)+1
 supported=sorted(fam,key=lambda f:fam[f],reverse=True)
 primary=supported[0] if supported else None
 return {"revision":"SSR_011","primary_money_hunt_family":primary,
  "physical_friction_family_counts":fam,
  "priority_rule":"FRICTION_SUPPORTED_FAMILIES_FIRST_THEN_UNSUPPORTED_OBSERVE_ONLY",
  "goal":"FIRST_PROSPECTIVE_OOS_X_PHYSICAL_FRICTION_NET_OUTCOME",
  "execution_authority":False,"read_only":True}

def write(root):
 d=policy(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/money_hunt_priority.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_011_money_hunt_priority import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_policy(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIsNotNone(d["primary_money_hunt_family"],"NO_PHYSICAL_FRICTION_SUPPORTED_FAMILY")
  self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-011 money-hunt priority policy")
  print("[PRIMARY]",d["primary_money_hunt_family"])
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
