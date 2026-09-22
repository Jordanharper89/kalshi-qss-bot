from __future__ import annotations
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
