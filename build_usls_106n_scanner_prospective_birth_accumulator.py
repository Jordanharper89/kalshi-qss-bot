from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106n_scanner_prospective_birth_accumulator.py"
TEST=ROOT/"test_usls_106n_scanner_prospective_birth_accumulator.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106k_scanner_raw_dual_lane_persistence_gate import run as persist_cycle
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106m_scanner_lifecycle_state_materializer import build as lifecycle_build

def run(root,cycles=5,seconds_per_cycle=12,max_rows=2000):
 started=time.time();history=[];birth_seen=False
 for i in range(1,cycles+1):
  r=persist_cycle(root,seconds=seconds_per_cycle,max_rows=max_rows)
  life=lifecycle_build(root)
  row={"cycle":i,"session_new_births":r["session_new_births"],
   "session_trade_rows":r["session_trade_rows"],
   "persisted_birth_rows":r["persisted_birth_rows"],
   "persisted_trade_rows":r["persisted_trade_rows"],
   "deduplicated_existing_rows":r["deduplicated_existing_rows"],
   "birth_lane_error":(r.get("birth_lane") or {}).get("error"),
   "trade_lane_error":r.get("trade_lane_error"),
   "tape_birth_rows":life["birth_record_count"],
   "tape_trade_rows":life["trade_record_count"],
   "joined_trade_count":life["joined_trade_count"],
   "unresolved_trade_count":life["unresolved_trade_count"]}
  history.append(row)
  if life["birth_record_count"]>0:
   birth_seen=True
   break
 life=lifecycle_build(root)
 return {"revision":"USLS_106N","cycles_requested":cycles,"cycles_completed":len(history),
  "seconds_per_cycle":seconds_per_cycle,"elapsed_seconds":time.time()-started,
  "history":history,"birth_seen":birth_seen,
  "birth_record_count":life["birth_record_count"],"trade_record_count":life["trade_record_count"],
  "joined_trade_count":life["joined_trade_count"],"unresolved_trade_count":life["unresolved_trade_count"],
  "state":"BIRTH_CAPTURED_READY_FOR_FIRST_TRADE_JOIN" if birth_seen else "WAITING_FOR_PROSPECTIVE_BIRTH",
  "accounting_ok":life["accounting_ok"],"lifecycle_join_certified":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,cycles=5,seconds_per_cycle=12,max_rows=2000):
 d=run(root,cycles,seconds_per_cycle,max_rows)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_prospective_birth_accumulator.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106n_scanner_prospective_birth_accumulator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_accumulator(self):
  p,d=write(ROOT,cycles=5,seconds_per_cycle=12,max_rows=2000)
  print("[STATE]",json.dumps({"state":d["state"],"cycles_completed":d["cycles_completed"],
   "elapsed_seconds":round(d["elapsed_seconds"],3),"birth_record_count":d["birth_record_count"],
   "trade_record_count":d["trade_record_count"],"joined_trade_count":d["joined_trade_count"],
   "unresolved_trade_count":d["unresolved_trade_count"],"accounting_ok":d["accounting_ok"]},sort_keys=True))
  for x in d["history"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  self.assertTrue(d["accounting_ok"],"LIFECYCLE_ACCOUNTING_LOSS")
  self.assertGreater(d["trade_record_count"],0,"NO_PERSISTED_TRADE_ACTIVITY")
  self.assertTrue(all(x["birth_lane_error"] is None for x in d["history"]),"BIRTH_LANE_ERROR")
  self.assertTrue(all(x["trade_lane_error"] is None for x in d["history"]),"TRADE_LANE_ERROR")
  self.assertFalse(d["lifecycle_join_certified"]);self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106N prospective scanner birth accumulator")
  if d["birth_seen"]:
   print("[READY] prospective birth captured on same persistent scanner tape")
  else:
   print("[WAIT] no prospective birth yet; rerun this same test later")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
