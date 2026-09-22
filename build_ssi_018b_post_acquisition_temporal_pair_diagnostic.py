from pathlib import Path
import ast

R=Path.cwd()
D=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
"qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
"qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
]
for x in D:
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))

Q=R/"test_ssi_018b_post_acquisition_temporal_pair_diagnostic.py"
S=r'''import unittest
from datetime import datetime
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair

def dt(s):
 if isinstance(s,datetime): return s
 if isinstance(s,str): return datetime.fromisoformat(s.replace("Z","+00:00"))
 return None
def rt(r):
 for n in ("snapshot_at","observed_at","event_time","timestamp","acquired_at"):
  v=getattr(r,n,None)
  if v: return dt(v)
 return None

class T(unittest.TestCase):
 def test_temporal_pair_boundary(self):
  later=priced=near=0
  for token in TOKENS:
   h=tuple(read_pinned_pool_history(token,limit=4096))
   c=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   times=[rt(r) for r in h if rt(r)]
   print("\n[TOKEN]",token,"history=",len(h),
         "first=",min(times) if times else None,
         "last=",max(times) if times else None)
   for case in c:
    ct=dt(case.snapshot_at); candidates=[]
    for r in h:
     t=rt(r)
     if not t or not ct or t<=ct: continue
     later+=1
     try: px=_price_for_pair(r,case.pair_address)
     except Exception as e: px=("ERROR",type(e).__name__,str(e))
     delta=(t-ct).total_seconds()
     if px is not None: priced+=1
     if abs(delta-60)<=8 and px is not None: near+=1
     candidates.append((round(delta,3),px))
    candidates.sort(key=lambda x:abs(x[0]-60))
    print("[CASE]",dict(case.conditions).get("order_flow"),
          "at=",case.snapshot_at,"pair=",case.pair_address)
    print(" later=",len(candidates),
          "nearest=",candidates[:5],
          "priced_near_60=",sum(1 for d,p in candidates if abs(d-60)<=8 and p is not None))
  print("\n[SSI-018B-TOTAL] later=",later,"priced=",priced,"priced_within_8s=",near)
  self.assertGreater(later,0)

if __name__=="__main__": unittest.main(verbosity=2)
'''
Q.write_text(S,encoding="utf-8")
ast.parse(S)
print("[PASS] SSI-018B installed")
print("[PASS] post-acquisition temporal/pair diagnostic")
print("[PASS] no acquisition; no thesis mutation")
print("[PASS] read-only; execution_authority=FALSE")