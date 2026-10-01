from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_016_persistent_pumpswap_money_state.py"
TEST=ROOT/"test_ssr_016_persistent_pumpswap_money_state.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

OOS="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
FRI="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"
FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/persistent_pumpswap_money_state.json"

def _load(root,rel):
 p=Path(root)/rel
 if not p.exists(): return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}

def _median(v):
 v=sorted(v);return None if not v else v[len(v)//2]

def build(root):
 root=Path(root);o=_load(root,OOS);f=_load(root,FRI);z=_load(root,FREEZE)
 cases=[x for x in o.get("cases",[]) if x.get("family")=="PUMP_SWAP" and isinstance(x.get("gross_forward_return"),(int,float))]
 vals=[float(x["gross_forward_return"]) for x in cases]
 rr=[x for x in f.get("ready_rows",[]) if x.get("family")=="PUMP_SWAP" and x.get("executable_ready")]
 fees=[float(x["fee_fraction"]) for x in rr if isinstance(x.get("fee_fraction"),(int,float))]
 devs=[abs(float(x["realized_execution_deviation_fraction"])) for x in rr if isinstance(x.get("realized_execution_deviation_fraction"),(int,float))]
 fee=_median(fees);dev=_median(devs);fr=None if fee is None or dev is None else 2*fee+2*dev
 gross=None if not vals else sum(vals)/len(vals);net=None if gross is None or fr is None else gross-fr
 freezes=[x for x in z.get("frozen_setups",[]) if x.get("family")=="PUMP_SWAP"]
 resolved={x.get("freeze_hash") for x in cases}
 return {"revision":"SSR_016","generated_unix":time.time(),"family":"PUMP_SWAP",
  "oos_case_count":len(cases),"positive_count":sum(v>0 for v in vals),
  "positive_frequency":None if not vals else sum(v>0 for v in vals)/len(vals),
  "mean_gross_return":gross,"physical_friction_row_count":len(rr),
  "modeled_round_trip_friction":fr,"estimated_mean_net_return":net,
  "frozen_setup_count":len(freezes),"pending_freeze_count":sum(x.get("freeze_hash") not in resolved for x in freezes),
  "ready_gate_case_target":5,"cases_needed_to_min_gate":max(0,5-len(cases)),
  "state":"READY_CANDIDATE" if len(cases)>=5 and isinstance(net,(int,float)) and net>0 and sum(v>0 for v in vals)/len(vals)>0.5 else "OBSERVE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_016_persistent_pumpswap_money_state import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_state(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["family"],"PUMP_SWAP");self.assertGreaterEqual(d["physical_friction_row_count"],1)
  self.assertFalse(d["execution_authority"]);print("[PASS] SSR-016 persistent PumpSwap money state")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
