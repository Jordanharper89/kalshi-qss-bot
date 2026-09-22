from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py"
TEST=ROOT/"test_ssi_002b_physical_exact_future_price_path_materialization.py"
MODULE=r"""
from dataclasses import dataclass
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair
def _dt(v):
 if isinstance(v,datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True)
class PricePath:
 pair_address:str; anchor_at:str; anchor_price:float; horizon_seconds:int
 observations:int; outcome_at:str; outcome_price:float; return_fraction:float
 mfe:float; mae:float; time_to_mfe_seconds:float; time_to_mae_seconds:float
 mfe_before_mae:bool; evidence_observation_ids:tuple
 read_only:bool=True; execution_authority:bool=False
def materialize_exact_future_price_paths(cases,records,horizons=(5,15,30,60,300,900,3600),tolerance_seconds=8.0):
 rows=tuple(sorted(records,key=lambda r:_dt(r.observed_at))); out=[]
 wanted=tuple(sorted({int(h) for h in horizons if int(h)>0}))
 for c in cases:
  evidence=set(c.evidence_observation_ids)
  anchors=[r for r in rows if r.observation_id in evidence]
  if not anchors: continue
  anchor=anchors[-1]; ap=_price_for_pair(anchor,c.pair_address)
  if ap is None or ap<=0: continue
  at=_dt(c.snapshot_at)
  future=[r for r in rows if _dt(r.observed_at)>at and _price_for_pair(r,c.pair_address) is not None]
  for h in wanted:
   end=at.timestamp()+h
   path=[r for r in future if _dt(r.observed_at).timestamp()<=end+float(tolerance_seconds)]
   eligible=[r for r in path if _dt(r.observed_at).timestamp()>=end]
   if not eligible: continue
   terminal=eligible[0]; terminal_t=_dt(terminal.observed_at)
   path=[r for r in path if _dt(r.observed_at)<=terminal_t]
   pts=[(r,_price_for_pair(r,c.pair_address)) for r in path]
   pts=[(r,float(px)) for r,px in pts if px is not None and float(px)>0]
   if not pts: continue
   rets=[(px/ap)-1.0 for _,px in pts]; hi=max(range(len(rets)),key=rets.__getitem__); lo=min(range(len(rets)),key=rets.__getitem__)
   op=pts[-1][1]
   out.append(PricePath(c.pair_address,str(c.snapshot_at),float(ap),h,len(pts),
    str(pts[-1][0].observed_at),op,(op/ap)-1.0,rets[hi],rets[lo],
    (_dt(pts[hi][0].observed_at)-at).total_seconds(),(_dt(pts[lo][0].observed_at)-at).total_seconds(),
    hi<lo,tuple(c.evidence_observation_ids)+tuple(r.observation_id for r,_ in pts)))
 return tuple(out)
"""
TEST_SOURCE=r"""
import unittest
from dataclasses import dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
@dataclass
class R: observation_id:str; observed_at:str; payload:dict
@dataclass
class C: pair_address:str; snapshot_at:str; evidence_observation_ids:tuple
class T(unittest.TestCase):
 def test_exact_path_semantics(self):
  def r(i,t,p): return R(i,t,{"pools":({"pair_address":"PAIR","price_usd":p},)})
  rows=(r("a","2026-09-01T00:00:00Z",100),r("b","2026-09-01T00:00:05Z",110),
        r("c","2026-09-01T00:00:10Z",95),r("d","2026-09-01T00:00:15Z",120))
  c=C("PAIR","2026-09-01T00:00:00Z",("a",))
  x=materialize_exact_future_price_paths((c,),rows,(15,),0)[0]
  print("[PATH]",x)
  self.assertEqual(x.observations,3);self.assertAlmostEqual(x.return_fraction,.20)
  self.assertAlmostEqual(x.mfe,.20);self.assertAlmostEqual(x.mae,-.05)
  self.assertEqual(x.time_to_mfe_seconds,15);self.assertEqual(x.time_to_mae_seconds,10)
  self.assertFalse(x.mfe_before_mae);self.assertFalse(x.execution_authority)
if __name__=="__main__": unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002B PHYSICAL EXACT FUTURE PRICE-PATH MATERIALIZATION INSTALLER");print("="*120)
 deps=["qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
 "qseries_v2/oracle_strategy_intelligence/solana/ssi_001e_solana_profitability_input_lineage_audit.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists(): raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] exact OAD-314 pair->price_usd contract reused")
 print("[PASS] future-only path + return/MFE/MAE/path-ordering materializer installed")
 print("[PASS] no acquisition, PostgreSQL connection, writer, GMGN, or execution authority")
 print("[DONE] SSI-002B INSTALLATION COMPLETE")
if __name__=="__main__": main()
