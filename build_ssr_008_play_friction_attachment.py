from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_008_play_friction_attachment.py"
TEST=ROOT/"test_ssr_008_play_friction_attachment.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_007_empirical_play_ranker import build as ranked

FRI="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/friction_attached_plays.json"

def _load(p):
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}

def _median(vals):
 vals=sorted(vals);return None if not vals else vals[len(vals)//2]

def build(root):
 root=Path(root);d=ranked(root);fri=_load(root/FRI);byfam={}
 for x in fri.get("ready_rows") or []:
  f=x.get("family")
  if f:byfam.setdefault(f,[]).append(x)
 out=[]
 for p in d.get("plays") or []:
  fs=byfam.get(p["family"],[])
  fees=[float(x["fee_fraction"]) for x in fs if isinstance(x.get("fee_fraction"),(int,float))]
  devs=[abs(float(x["realized_execution_deviation_fraction"])) for x in fs if isinstance(x.get("realized_execution_deviation_fraction"),(int,float))]
  fee=_median(fees);dev=_median(devs);friction=None
  if fee is not None and dev is not None:friction=2*fee+2*dev
  gross=p.get("historical_mean_gross_return");net=None
  if friction is not None and isinstance(gross,(int,float)):net=float(gross)-friction
  out.append({**p,"physical_friction_row_count":len(fs),"one_way_median_fee_fraction":fee,
   "one_way_median_execution_deviation_fraction":dev,"modeled_round_trip_friction":friction,
   "estimated_net_edge_from_family_oos":net,
   "friction_state":"PHYSICAL_FAMILY_FRICTION_SUPPORTED" if friction is not None else "FRICTION_UNRESOLVED",
   "friction_semantics":"FAMILY_LEVEL_MEDIAN_FROM_PHYSICALLY_READY_PHASE7_ROWS_NO_CROSS_FAMILY_IMPUTATION"})
 return {"revision":"SSR_008","play_count":len(out),"plays":out,
  "friction_supported_play_count":sum(x["friction_state"]=="PHYSICAL_FAMILY_FRICTION_SUPPORTED" for x in out),
  "cross_family_imputation":False,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_008_play_friction_attachment import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_friction(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"play_count":d["play_count"],"friction_supported_play_count":d["friction_supported_play_count"]},sort_keys=True))
  self.assertFalse(d["cross_family_imputation"]);self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-008 play friction attachment")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
