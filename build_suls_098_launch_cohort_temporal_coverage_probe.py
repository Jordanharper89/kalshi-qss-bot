from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_098_launch_cohort_temporal_coverage_probe.py"
TEST=ROOT/"test_suls_098_launch_cohort_temporal_coverage_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

def probe(root,limit=512):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 d=json.loads((b/"confirmed_tradeable_birth_events.json").read_text(encoding="utf-8"))
 rows=[];covered=0;priced=0
 for e in d.get("events",[]):
  token=e.get("token_address");pair=e.get("pair_address")
  hist=tuple(read_pinned_pool_history(token,root=root,limit=limit)) if token else ()
  hp=[]
  for r in hist:
   pools=tuple((r.payload or {}).get("pools") or ())
   if pair and any(str(p.get("pair_address") or "")==str(pair) and p.get("price_usd") is not None for p in pools):
    hp.append(r)
  if hist:covered+=1
  if hp:priced+=1
  rows.append({"signature":e.get("signature"),"token_address":token,"pair_address":pair,
   "history_records":len(hist),"priced_pair_records":len(hp),
   "first_observed_at":hist[0].observed_at if hist else None,
   "last_observed_at":hist[-1].observed_at if hist else None})
 return {"revision":"SULS_098","event_count":len(rows),"history_covered_events":covered,
  "priced_pair_covered_events":priced,"rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=probe(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/launch_cohort_temporal_coverage.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_098_launch_cohort_temporal_coverage_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="rows"},sort_keys=True))
  for r in d["rows"][:40]:print("[ROW]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["event_count"],0)
  print("[PASS] SULS-098 launch-cohort temporal coverage probe")
  print("[SCOPE] Diagnostic only; zero coverage is a valid physical result")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")