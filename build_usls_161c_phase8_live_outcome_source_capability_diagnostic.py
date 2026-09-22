from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161c_phase8_live_outcome_source_capability_diagnostic.py"
TEST=ROOT/"test_usls_161c_phase8_live_outcome_source_capability_diagnostic.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time
from pathlib import Path

PRICE_KEYS=("effective_price","price","price_usd","execution_price")
MARKET_KEYS=("market_address","pool","pool_address","curve","curve_address")
FAMILY_KEYS=("family","venue","program_family","source_family")
TIME_KEYS=("observed_unix","trade_observed_unix","received_unix","scanner_observed_unix","block_time")
SIG_KEYS=("signature","trade_signature")

def _rows(v):
 if isinstance(v,list):return v
 if isinstance(v,dict):
  for k in ("rows","events","notifications","captured","raw_rows"):
   if isinstance(v.get(k),list):return v[k]
 return []

def _first(x,keys):
 if not isinstance(x,dict):return None
 for k in keys:
  v=x.get(k)
  if v not in (None,""):return v
 return None

async def _capture():
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await capture(seconds=15,max_rows=8000)

def run(root):
 started=time.time();ret=asyncio.run(_capture());ended=time.time()
 rows=_rows(ret);out=[];fam={}
 for x in rows:
  family=str(_first(x,FAMILY_KEYS) or "UNKNOWN").upper()
  market=_first(x,MARKET_KEYS);price=_first(x,PRICE_KEYS)
  ts=_first(x,TIME_KEYS);sig=_first(x,SIG_KEYS)
  rec={"family":family,"market_address":market,"price":price,
       "observed_time":ts,"trade_signature":sig,
       "has_family":family!="UNKNOWN","has_market":market is not None,
       "has_price":price is not None,"has_time":ts is not None,
       "has_signature":sig is not None}
  out.append(rec)
  z=fam.setdefault(family,{"rows":0,"market":0,"price":0,"time":0,"signature":0,
                           "fully_observable":0})
  z["rows"]+=1;z["market"]+=rec["has_market"];z["price"]+=rec["has_price"]
  z["time"]+=rec["has_time"];z["signature"]+=rec["has_signature"]
  z["fully_observable"]+=all((rec["has_market"],rec["has_price"],rec["has_time"],rec["has_signature"]))
 ready=[f for f,v in fam.items() if v["fully_observable"]>0 and f!="UNKNOWN"]
 return {"revision":"USLS_161C","elapsed_seconds":ended-started,
  "raw_row_count":len(rows),"family_support":fam,
  "families_with_live_price_outcome_source":sorted(ready),
  "ready_family_count":len(ready),
  "sample_rows":out[:200],
  "diagnostic_conclusion":
   "PROSPECTIVE_PHASE8_OUTCOMES_REQUIRE_LIVE_FAMILY_MARKET_PRICE_TIME_SIGNATURE_ROWS",
  "next_boundary":(
   "PROSPECTIVE_FEATURE_FREEZE_AND_FORWARD_OUTCOME_COLLECTION"
   if ready else
   "WIRE_LIVE_EXACT_TRADE_ECONOMICS_INTO_PHASE8_OUTCOME_SOURCE"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_live_outcome_source_capability_diagnostic.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161c_phase8_live_outcome_source_capability_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"raw_row_count":d["raw_row_count"],
   "ready_family_count":d["ready_family_count"],
   "families_with_live_price_outcome_source":d["families_with_live_price_outcome_source"],
   "family_support":d["family_support"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["raw_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161C live outcome-source capability diagnostic")
  print("[PASS] measured whether live rows can support prospective price outcomes before building learner")
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
