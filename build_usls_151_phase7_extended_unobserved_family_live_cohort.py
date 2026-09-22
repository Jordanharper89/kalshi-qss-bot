from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_151_phase7_extended_unobserved_family_live_cohort.py"
TEST=ROOT/"test_usls_151_phase7_extended_unobserved_family_live_cohort.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time
from pathlib import Path

TARGET={"METEORA_DAMM_V1","METEORA_DAMM_V2","MOONIT","BOOP_FUN","HEAVEN"}

def _rows(v):
 if isinstance(v,list):return v
 if isinstance(v,dict):
  for k in ("rows","events","notifications","captured","raw_rows"):
   if isinstance(v.get(k),list):return v[k]
 return []

def _first(x,*keys):
 if not isinstance(x,dict):return None
 for k in keys:
  v=x.get(k)
  if v not in (None,""):return v
 return None

async def _capture():
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await capture(seconds=30,max_rows=12000)

def run(root):
 started=time.time();ret=asyncio.run(_capture());ended=time.time()
 rows=_rows(ret);kept=[];fam={}
 for x in rows:
  f=str(_first(x,"family","venue","program_family","source_family") or "").upper()
  if f not in TARGET:continue
  sig=_first(x,"signature","trade_signature")
  obs=_first(x,"observed_unix","trade_observed_unix","received_unix","scanner_observed_unix") or ended
  kept.append({"family":f,"trade_signature":sig,"observed_unix":obs,
   "captured_unix":ended,"raw":x,"execution_authority":False})
  fam[f]=fam.get(f,0)+1
 return {"revision":"USLS_151","elapsed_seconds":ended-started,"raw_row_count":len(rows),
  "target_row_count":len(kept),"target_family_counts":fam,
  "missing_target_families":sorted(TARGET-set(fam)),"rows":kept,
  "prospective":True,"next_boundary":"PHASE7_ROLE_AND_COVERAGE_CHECKPOINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_extended_unobserved_family_live_cohort.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_151_phase7_extended_unobserved_family_live_cohort import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"raw_row_count":d["raw_row_count"],
   "target_row_count":d["target_row_count"],"target_family_counts":d["target_family_counts"],
   "missing_target_families":d["missing_target_families"],
   "elapsed_seconds":d["elapsed_seconds"]},sort_keys=True))
  self.assertGreater(d["raw_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY")
  self.assertTrue(d["prospective"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-151 extended unobserved-family live cohort")
  print("[STATE] target families may remain absent if no live activity occurred in bounded window")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
