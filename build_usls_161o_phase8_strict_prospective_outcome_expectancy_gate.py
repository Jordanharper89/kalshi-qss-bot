from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161o_phase8_strict_prospective_outcome_expectancy_gate.py"
TEST=ROOT/"test_usls_161o_phase8_strict_prospective_outcome_expectancy_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161m_phase8_bounded_live_direct_economics_gate import run as live_run
FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_prospective_freezes.json"

def _rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in ("ready_rows","rows","trades","normalized_rows"):
   if isinstance(x.get(k),list):return x[k]
 return []

def _friction(root):
 by={}
 for p in (Path(root)/"runtime_state/solana_opportunities").rglob("*.json"):
  try:d=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
  except Exception:continue
  for r in _rows(d):
   fam=str(r.get("family") or r.get("venue") or "").upper()
   fee=r.get("fee_fraction");dev=r.get("realized_execution_deviation_fraction")
   if isinstance(fee,(int,float)) and isinstance(dev,(int,float)):
    q=by.setdefault(fam,{"fee":[],"dev":[]});q["fee"].append(float(fee));q["dev"].append(abs(float(dev)))
 def med(v):v=sorted(v);return None if not v else v[len(v)//2]
 return {f:{"n":len(v["fee"]),"fee":med(v["fee"]),"dev":med(v["dev"])} for f,v in by.items()}

def run(root):
 root=Path(root);frz=json.loads((root/FREEZE).read_text(encoding="utf-8"));time.sleep(5)
 live=live_run(root,seconds=32,max_rows=24000,max_sigs=36)
 by={}
 for x in live.get("rows",[]):
  k=(x["family"],str(x["market_address"]),x["input_asset"],x["output_asset"])
  by.setdefault(k,[]).append(x)
 cases=[]
 for s in frz.get("frozen_setups",[]):
  k=(s["family"],str(s["market_address"]),s["input_asset"],s["output_asset"])
  xs=[x for x in by.get(k,[]) if x["observed_unix"]>s["freeze_unix"]]
  if not xs:continue
  x=min(xs,key=lambda z:z["observed_unix"]);p0=float(s["last_price"]);p1=float(x["effective_output_per_input"])
  cases.append({"freeze_hash":s["freeze_hash"],"family":s["family"],"market_address":s["market_address"],
   "input_asset":s["input_asset"],"output_asset":s["output_asset"],"freeze_unix":s["freeze_unix"],
   "later_observed_unix":x["observed_unix"],"entry_reference_price":p0,"later_price":p1,
   "gross_forward_return":p1/p0-1 if p0 else None,"execution_authority":False})
 friction=_friction(root);net=[]
 for c in cases:
  f=friction.get(c["family"]);g=c["gross_forward_return"]
  if f and f["fee"] is not None and f["dev"] is not None and isinstance(g,(int,float)):
   cost=2*f["fee"]+2*f["dev"];net.append({**c,"modeled_round_trip_friction":cost,"net_forward_return":g-cost})
 fams=sorted({c["family"] for c in cases});netf=sorted({c["family"] for c in net})
 gv=[c["gross_forward_return"] for c in cases if isinstance(c["gross_forward_return"],(int,float))]
 nv=[c["net_forward_return"] for c in net]
 decision=("NO_PROSPECTIVE_CASES" if not gv else "INSUFFICIENT_NET_FRICTION_SAMPLE" if len(nv)<5 else
  "POSITIVE_NET_EXPECTANCY_OBSERVED_NOT_YET_CERTIFIED" if sum(nv)/len(nv)>0 else "NO_POSITIVE_NET_EXPECTANCY_OBSERVED")
 return {"revision":"USLS_161O","prospective_case_count":len(cases),"prospective_families":fams,
  "mean_gross_forward_return":None if not gv else sum(gv)/len(gv),"gross_positive_frequency":None if not gv else sum(v>0 for v in gv)/len(gv),
  "net_case_count":len(net),"net_friction_families":netf,"mean_net_forward_return":None if not nv else sum(nv)/len(nv),
  "net_positive_frequency":None if not nv else sum(v>0 for v in nv)/len(nv),"cases":cases,"net_cases":net,
  "profitability_decision":decision,"universal_phase8_complete":False,
  "next_boundary":"EXPAND_PENDING_FAMILIES_AND_ACCUMULATE_PROSPECTIVE_OOS_BEFORE_PHASE8_CERTIFICATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_strict_prospective_expectancy.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161o_phase8_strict_prospective_outcome_expectancy_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"prospective_case_count":d["prospective_case_count"],
   "prospective_families":d["prospective_families"],"mean_gross_forward_return":d["mean_gross_forward_return"],
   "net_case_count":d["net_case_count"],"net_friction_families":d["net_friction_families"],
   "mean_net_forward_return":d["mean_net_forward_return"],"profitability_decision":d["profitability_decision"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["prospective_case_count"],0,"NO_STRICTLY_LATER_SAME_MARKET_SAME_PAIR_PROSPECTIVE_CASES")
  self.assertFalse(d["universal_phase8_complete"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161O strict prospective outcome + expectancy gate")
  print("[PASS] forward returns use only strictly later same-market same-directed-pair live economics")
  print("[PASS] net expectancy only where physical friction evidence exists")
  print("[STATE]",d["profitability_decision"])
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
