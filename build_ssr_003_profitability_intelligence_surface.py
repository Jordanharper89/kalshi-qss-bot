from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_003_profitability_intelligence.py"
TEST=ROOT/"test_ssr_003_profitability_intelligence_surface.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
LED="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
NET="runtime_state/solana_opportunities/solana_scanner/phase8_learning_net_intersection_checkpoint.json"
def _load(root,rel):
 p=Path(root)/rel
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}
def build(root):
 root=Path(root);led=_load(root,LED);net=_load(root,NET);cases=led.get("cases") or []
 gross=[float(x["gross_forward_return"]) for x in cases if isinstance(x.get("gross_forward_return"),(int,float))]
 fam={}
 for x in cases:
  f=x.get("family","UNKNOWN");z=fam.setdefault(f,{"n":0,"returns":[]});z["n"]+=1
  if isinstance(x.get("gross_forward_return"),(int,float)):z["returns"].append(float(x["gross_forward_return"]))
 groups=[]
 for f,z in fam.items():
  vals=z["returns"];groups.append({"family":f,"sample_size":z["n"],"mean_gross_return":None if not vals else sum(vals)/len(vals),
   "positive_frequency":None if not vals else sum(v>0 for v in vals)/len(vals)})
 groups.sort(key=lambda x:(x["sample_size"],x["mean_gross_return"] if x["mean_gross_return"] is not None else -999),reverse=True)
 friction_n=int(net.get("friction_supported_case_count") or 0);mean_net=net.get("mean_net_forward_return")
 if friction_n<5:play_state="OBSERVE"
 elif isinstance(mean_net,(int,float)) and mean_net>0:play_state="CANDIDATE_EDGE_NOT_CERTIFIED"
 else:play_state="ABSTAIN"
 return {"revision":"SSR_003","updated_unix":time.time(),"prospective_case_count":len(cases),
  "gross_mean":None if not gross else sum(gross)/len(gross),"gross_positive_frequency":None if not gross else sum(v>0 for v in gross)/len(gross),
  "friction_supported_case_count":friction_n,"mean_net_forward_return":mean_net,"net_expectancy_status":net.get("net_expectancy_status"),
  "family_groups":groups,"play_state":play_state,
  "money_question":"WOULD_THE_OBSERVED_SETUP_HAVE_MADE_MONEY_AFTER_SUPPORTED_EXECUTION_FRICTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/profitability_intelligence.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_003_profitability_intelligence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_surface(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn(d["play_state"],("OBSERVE","CANDIDATE_EDGE_NOT_CERTIFIED","ABSTAIN"))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-003 profitability intelligence surface")
  print("[STATE] play_state="+d["play_state"])
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")