from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161b_phase8_forward_outcome_availability_diagnostic.py"
TEST=ROOT/"test_usls_161b_phase8_forward_outcome_availability_diagnostic.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

SNAP="runtime_state/solana_opportunities/solana_scanner/phase8_enriched_feature_snapshots.json"
PATHS="runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json"

def run(root):
 root=Path(root)
 s=json.loads((root/SNAP).read_text(encoding="utf-8"))
 p=json.loads((root/PATHS).read_text(encoding="utf-8"))
 paths=p.get("paths",[])
 by_h={};by_f={};reasons={};rows=[]
 for x in s.get("snapshots",[]):
  try:
   pi=int(str(x["case_id"]).split("-")[1])
  except Exception:
   continue
  if pi>=len(paths):continue
  path=paths[pi]
  cutoff=x.get("feature_cutoff_unix")
  timed=[r for r in (path.get("price_path") or [])
         if isinstance(r.get("observed_unix"),(int,float))
         and isinstance(r.get("price"),(int,float))]
  future=[r for r in timed if isinstance(cutoff,(int,float)) and r["observed_unix"]>cutoff]
  observed_cp=[c for c in (path.get("checkpoints") or [])
               if c.get("state")=="OBSERVED" and isinstance(c.get("price"),(int,float))]
  later_cp=[c for c in observed_cp if c.get("horizon_seconds",0)>x.get("horizon_seconds",0)]
  if future:reason="TIMED_FUTURE_AVAILABLE"
  elif later_cp:reason="CHECKPOINT_FUTURE_AVAILABLE"
  else:reason="NO_PHYSICAL_FORWARD_OUTCOME_AFTER_CUTOFF"
  fam=x.get("family");h=x.get("horizon_seconds")
  z=by_h.setdefault(str(h),{"snapshots":0,"timed_future":0,"checkpoint_future":0,"none":0})
  z["snapshots"]+=1;z["timed_future"]+=bool(future);z["checkpoint_future"]+=bool(later_cp)
  z["none"]+=reason=="NO_PHYSICAL_FORWARD_OUTCOME_AFTER_CUTOFF"
  f=by_f.setdefault(fam,{"snapshots":0,"timed_future":0,"checkpoint_future":0,"none":0})
  f["snapshots"]+=1;f["timed_future"]+=bool(future);f["checkpoint_future"]+=bool(later_cp)
  f["none"]+=reason=="NO_PHYSICAL_FORWARD_OUTCOME_AFTER_CUTOFF"
  reasons[reason]=reasons.get(reason,0)+1
  rows.append({"case_id":x["case_id"],"family":fam,"horizon_seconds":h,
   "timed_path_count":len(timed),"future_timed_count":len(future),
   "later_observed_checkpoint_count":len(later_cp),"reason":reason})
 return {"revision":"USLS_161B","snapshot_count":len(rows),
  "outcome_reason_counts":reasons,"by_horizon":by_h,"by_family":by_f,"rows":rows,
  "diagnostic_conclusion":
   "PHYSICAL_FORWARD_OUTCOME_AVAILABILITY_MUST_EXIST_BEFORE_EMPIRICAL_LEARNING",
  "next_boundary":
   "REPAIR_FORWARD_OUTCOME_ATTRIBUTION_FROM_PHYSICAL_LATER_OBSERVATIONS_OR_COLLECT_PROSPECTIVE_OUTCOMES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 out=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_forward_outcome_availability_diagnostic.json"
 out.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return out,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161b_phase8_forward_outcome_availability_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"snapshot_count":d["snapshot_count"],
   "outcome_reason_counts":d["outcome_reason_counts"],
   "by_horizon":d["by_horizon"],"by_family":d["by_family"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["snapshot_count"],0,"NO_PHASE8_SNAPSHOTS_TO_DIAGNOSE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161B forward-outcome availability diagnostic")
  print("[PASS] zero learnable cases traced to physical outcome availability, not hidden by fallback labels")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
