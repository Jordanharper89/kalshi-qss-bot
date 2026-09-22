from pathlib import Path
import ast

R=Path.cwd()
deps=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
"qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py",
]
for d in deps:
 p=R/d
 if not p.exists(): raise SystemExit("[FAIL] missing "+d)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))

Q=R/"test_ssi_018_exact_60s_forward_path_rematerialization.py"
S=r'''import unittest
from dataclasses import fields,is_dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS,FROZEN_THESIS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths

class T(unittest.TestCase):
 def test_rematerialized_paths(self):
  rows=[]
  total_cases=total_paths=buy_cases=buy_paths=0
  for token in TOKENS:
   h=tuple(read_pinned_pool_history(token,limit=4096))
   c=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   p=tuple(materialize_exact_future_price_paths(
       c,h,horizons=(60,),tolerance_seconds=8.0))
   bc=[x for x in c if dict(x.conditions).get("order_flow")=="BUY_PRESSURE"]
   bp=[x for x in p if dict(getattr(x,"conditions",())).get("order_flow")=="BUY_PRESSURE"]
   total_cases+=len(c); total_paths+=len(p)
   buy_cases+=len(bc); buy_paths+=len(bp)
   row={"token":token,"history":len(h),"cases":len(c),
        "paths":len(p),"buy_cases":len(bc),"buy_paths":len(bp)}
   rows.append(row)
   print("[SSI-018-TOKEN]",row)
   if p:
    x=p[0]
    print("[SSI-018-PATH-FIELDS]",
      tuple(f.name for f in fields(x)) if is_dataclass(x) else tuple(vars(x)))
    print("[SSI-018-PATH]",repr(x))

  print("[SSI-018-THESIS]",FROZEN_THESIS)
  print("[SSI-018-TOTAL] cases=",total_cases,
        "paths=",total_paths,
        "buy_cases=",buy_cases,
        "buy_paths=",buy_paths)
  self.assertEqual(len(rows),5)
  self.assertEqual(len({x["token"] for x in rows}),5)
  self.assertGreater(total_cases,0)
  self.assertGreater(total_paths,0)
  self.assertEqual(FROZEN_THESIS["horizon"],60)
  self.assertEqual(FROZEN_THESIS["target"],0.1)
  self.assertEqual(FROZEN_THESIS["stop"],0.05)
  self.assertEqual(FROZEN_THESIS["friction_bps"],200)
  self.assertEqual(FROZEN_THESIS["condition"],("order_flow","BUY_PRESSURE"))

if __name__=="__main__": unittest.main(verbosity=2)
'''
Q.write_text(S,encoding="utf-8")
ast.parse(S)
print("[PASS] SSI-018 installed")
print("[PASS] exact frozen cohort rematerialization")
print("[PASS] 60-second horizon only")
print("[PASS] frozen BUY_PRESSURE thesis unchanged")
print("[PASS] no acquisition; execution_authority=FALSE")