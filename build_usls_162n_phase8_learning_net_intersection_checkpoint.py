from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162n_phase8_learning_net_intersection_checkpoint.py"
TEST=ROOT/"test_usls_162n_phase8_learning_net_intersection_checkpoint.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161r_phase8_prospective_feature_outcome_empirical_learner import run as learn
LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
FRIC="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"

def run(root):
 root=Path(root);led=json.loads((root/LEDGER).read_text(encoding="utf-8"));f=json.loads((root/FRIC).read_text(encoding="utf-8"))
 l=learn(root);ready=f.get("ready_rows",[]);byfam={}
 for x in ready:
  if x.get("family"):byfam.setdefault(x["family"],[]).append(x)
 rows=[]
 for c in led.get("cases",[]):
  fs=byfam.get(c["family"],[])
  fees=[float(x["fee_fraction"]) for x in fs if isinstance(x.get("fee_fraction"),(int,float))]
  devs=[abs(float(x["realized_execution_deviation_fraction"])) for x in fs if isinstance(x.get("realized_execution_deviation_fraction"),(int,float))]
  fee=sorted(fees)[len(fees)//2] if fees else None;dev=sorted(devs)[len(devs)//2] if devs else None
  net=None
  if fee is not None and dev is not None and isinstance(c.get("gross_forward_return"),(int,float)):
   net=float(c["gross_forward_return"])-(2*fee+2*dev)
  rows.append({"family":c["family"],"freeze_hash":c["freeze_hash"],"gross_forward_return":c.get("gross_forward_return"),
   "net_forward_return":net,"physical_friction_supported":net is not None})
 net=[x["net_forward_return"] for x in rows if isinstance(x.get("net_forward_return"),(int,float))]
 fam={}
 for x in led.get("cases",[]):fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_162N","prospective_oos_case_count":len(rows),"family_case_counts":fam,
  "learned_group_count":l["learned_group_count"],"friction_supported_case_count":len(net),
  "friction_supported_families":sorted({x["family"] for x in rows if x["physical_friction_supported"]}),
  "mean_net_forward_return":None if not net else sum(net)/len(net),
  "net_positive_frequency":None if not net else sum(v>0 for v in net)/len(net),
  "net_expectancy_status":"INSUFFICIENT_PHYSICAL_FRICTION_INTERSECTION" if len(net)<5 else
   ("POSITIVE_NET_EXPECTANCY_OBSERVED_NOT_YET_CERTIFIED" if sum(net)/len(net)>0 else "NO_POSITIVE_NET_EXPECTANCY_OBSERVED"),
  "phase8_status":"IN_PROGRESS","next_boundary":"ACCUMULATE_TO_5_PER_FAMILY_AND_EXPAND_PHASE7_STRICT_FRICTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_learning_net_intersection_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162n_phase8_learning_net_intersection_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["prospective_oos_case_count"],0)
  self.assertGreater(d["learned_group_count"],0)
  self.assertEqual(d["phase8_status"],"IN_PROGRESS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162N learning + net-friction intersection checkpoint")
  print("[STATE]",d["net_expectancy_status"])
  print("[NEXT]",d["next_boundary"])
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
