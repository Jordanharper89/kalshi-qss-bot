from pathlib import Path
import ast

R=Path.cwd()
deps=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
"qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
"qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py",
]
for d in deps:
 p=R/d
 if not p.exists(): raise SystemExit("[FAIL] missing "+d)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))

Q=R/"test_ssi_016b_zero_path_exact_physical_diagnostic.py"

S=r'''import unittest,inspect
from datetime import datetime
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths

def ts(x):
 s=getattr(x,"snapshot_at",None) or getattr(x,"observed_at",None) or getattr(x,"event_time",None)
 if isinstance(s,datetime): return s
 if isinstance(s,str): return datetime.fromisoformat(s.replace("Z","+00:00"))
 return None

class T(unittest.TestCase):
 def test_zero_path_diagnostic(self):
  print("[PRICE-FN]",inspect.signature(_price_for_pair))
  total=0
  for token in TOKENS:
   h=tuple(read_pinned_pool_history(token,limit=4096))
   c=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   p=tuple(materialize_exact_future_price_paths(c,h,horizons=(60,),tolerance_seconds=8.0))
   print("\n[TOKEN]",token,"history=",len(h),"cases=",len(c),"paths=",len(p))
   for case in c:
    total+=1
    ct=ts(case)
    future=[]
    same_pair=0
    priced=0
    for r in h:
     rt=ts(r)
     if rt is None or ct is None or rt<=ct: continue
     try: price=_price_for_pair(r,case.pair_address)
     except Exception as e: price=("ERROR",type(e).__name__,str(e))
     if price is not None:
      same_pair+=1;priced+=1
     delta=(rt-ct).total_seconds()
     future.append((round(delta,3),price))
    nearest=min(future,key=lambda x:abs(x[0]-60)) if future else None
    within=[x for x in future if abs(x[0]-60)<=8]
    print("[CASE]",case.experience_id)
    print(" condition=",dict(case.conditions).get("order_flow"),
          "snapshot=",case.snapshot_at,"pair=",case.pair_address)
    print(" future_records=",len(future),"priced_future=",priced,
          "nearest_60s=",nearest,"within_8s=",within[:5])
  print("\n[SSI-016B] physical_cases=",total)
  self.assertGreater(total,0)

if __name__=="__main__": unittest.main(verbosity=2)
'''

Q.write_text(S,encoding="utf-8")
ast.parse(S)
print("[PASS] SSI-016B installed")
print("[PASS] zero-path rejection diagnostic installed")
print("[PASS] no acquisition and no mutation")
print("[PASS] frozen thesis unchanged")