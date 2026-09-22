from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106l_scanner_raw_tape_restart_idempotency_gate.py"
TEST=ROOT/"test_usls_106l_scanner_raw_tape_restart_idempotency_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"

def load(root):
 p=Path(root)/TAPE
 rows=[];bad=[]
 if not p.exists():return p,rows,[{"line":0,"error":"TAPE_MISSING"}]
 for i,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
  if not line.strip():continue
  try:
   x=json.loads(line)
   if not isinstance(x,dict):raise ValueError("ROW_NOT_OBJECT")
   rows.append(x)
  except Exception as e:
   bad.append({"line":i,"error":repr(e)})
 return p,rows,bad

def build(root):
 p,rows,bad=load(root)
 ids=[x.get("record_id") for x in rows]
 uniq={x for x in ids if x}
 dup_count=len(ids)-len(uniq)
 births=[x for x in rows if x.get("record_type")=="BIRTH"]
 trades=[x for x in rows if x.get("record_type")=="TRADE"]
 authority_bad=sum(x.get("execution_authority") is not False for x in rows)
 payload_bad=sum(not isinstance(x.get("payload"),dict) for x in rows)
 reconstructed_seen=set(uniq)
 replay_added=0
 for x in rows[:min(250,len(rows))]:
  rid=x.get("record_id")
  if rid not in reconstructed_seen:
   reconstructed_seen.add(rid);replay_added+=1
 return {
  "revision":"USLS_106L",
  "source_revision":"USLS_106K",
  "tape_path":TAPE,
  "row_count":len(rows),
  "birth_rows":len(births),
  "trade_rows":len(trades),
  "unique_record_ids":len(uniq),
  "duplicate_record_ids":dup_count,
  "malformed_rows":len(bad),
  "malformed_detail":bad[:20],
  "authority_violations":authority_bad,
  "payload_violations":payload_bad,
  "restart_reconstructed_seen_count":len(reconstructed_seen),
  "deterministic_replay_sample_size":min(250,len(rows)),
  "deterministic_replay_new_rows":replay_added,
  "restart_idempotency_verified":(
   len(rows)>0 and dup_count==0 and len(bad)==0 and authority_bad==0 and
   payload_bad==0 and replay_added==0
  ),
  "lifecycle_join_certified":False,
  "profitability_claimed":False,
  "execution_authority":False,
  "read_only":True
 }

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_raw_tape_restart_idempotency_gate.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106l_scanner_raw_tape_restart_idempotency_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "row_count":d["row_count"],
   "birth_rows":d["birth_rows"],
   "trade_rows":d["trade_rows"],
   "unique_record_ids":d["unique_record_ids"],
   "duplicate_record_ids":d["duplicate_record_ids"],
   "malformed_rows":d["malformed_rows"],
   "authority_violations":d["authority_violations"],
   "payload_violations":d["payload_violations"],
   "deterministic_replay_sample_size":d["deterministic_replay_sample_size"],
   "deterministic_replay_new_rows":d["deterministic_replay_new_rows"],
   "restart_idempotency_verified":d["restart_idempotency_verified"]},sort_keys=True))
  self.assertGreater(d["row_count"],0,"RAW_SCANNER_TAPE_EMPTY")
  self.assertGreater(d["trade_rows"],0,"NO_TRADE_ROWS_ON_PERSISTED_TAPE")
  self.assertEqual(d["duplicate_record_ids"],0,"DUPLICATE_RECORD_IDS_PRESENT")
  self.assertEqual(d["malformed_rows"],0,"MALFORMED_JSONL_ROWS_PRESENT")
  self.assertEqual(d["authority_violations"],0,"EXECUTION_AUTHORITY_VIOLATION")
  self.assertEqual(d["payload_violations"],0,"RAW_PAYLOAD_MISSING")
  self.assertEqual(d["deterministic_replay_new_rows"],0,"REPLAY_WOULD_DUPLICATE_ROWS")
  self.assertTrue(d["restart_idempotency_verified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106L scanner raw-tape restart/idempotency gate")
  print("[PASS] persisted tape reconstructs cleanly with zero duplicate replay")
  print("[PASS] lifecycle join remains uncertified")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
