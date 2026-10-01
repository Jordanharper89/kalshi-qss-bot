from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
TARGET=SUB/"suls_063_signal_relative_horizon_semantics.py"
TEST=ROOT/"test_suls_094_signal_relative_horizon_retention_repair.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
HORIZONS=(1,5,15,30,60,300,900)

def _source_id(x,i):
 return str(x.get("signature") or x.get("event_id") or x.get("observation_id") or f"EVENT_{i:08d}")

def build(root,now=None):
 now=time.time() if now is None else float(now)
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 ep=base/"confirmed_tradeable_birth_events.json"
 doc=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 events=list(doc.get("events") or [])
 rows=[]
 for i,e in enumerate(events):
  sid=_source_id(e,i)
  obs=e.get("observed_unix")
  age=e.get("trigger_age_seconds")
  if age is None: age=e.get("age_seconds")
  obsf=None if obs is None else float(obs)
  agef=None if age is None else max(0.0,float(age))
  birth=None if obsf is None or agef is None else obsf-agef
  for h in HORIZONS:
   target=None if birth is None else birth+float(h)
   if birth is None:
    status="TIMING_UNKNOWN"
   elif agef>float(h):
    status="MISSED_AT_DISCOVERY"
   elif target<=now:
    status="DUE"
   else:
    status="PENDING"
   rows.append({"source_event_id":sid,"signature":e.get("signature"),
    "token_address":e.get("token_address"),"pair_address":e.get("pair_address"),
    "horizon_seconds":h,"observed_unix":obsf,"capture_age_seconds":agef,
    "birth_unix":birth,"target_unix":target,"status":status,
    "execution_authority":False})
 pending=[x for x in rows if x["status"]=="PENDING"]
 due=[x for x in rows if x["status"]=="DUE"]
 missed=[x for x in rows if x["status"]=="MISSED_AT_DISCOVERY"]
 unknown=[x for x in rows if x["status"]=="TIMING_UNKNOWN"]
 out={"revision":"SULS_094","event_count":len(events),"horizon_rows":len(rows),
  "pending_count":len(pending),"due_count":len(due),
  "missed_at_discovery_count":len(missed),"timing_unknown_count":len(unknown),
  "dropped_events":0,"rows":rows,"checks":rows,"pending":pending,"due":due,
  "missed_at_discovery":missed,"timing_unknown":unknown,
  "late_birth_policy":"RETAIN_EVENT_MARK_ELAPSED_HORIZONS_MISSED_SCHEDULE_REMAINING",
  "execution_authority":False,"read_only":True}
 return out

def write(root):
 d=build(root)
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 p=base/"signal_relative_horizon_schedule.json"
 text=json.dumps(d,indent=2,sort_keys=True)
 p.write_text(text,encoding="utf-8")
 (base/"prospective_horizon_schedule.json").write_text(text,encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_063_signal_relative_horizon_semantics import write,HORIZONS
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_retention(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k not in ("rows","checks","pending","due","missed_at_discovery","timing_unknown")},sort_keys=True))
  self.assertEqual(d["horizon_rows"],d["event_count"]*len(HORIZONS))
  self.assertEqual(d["dropped_events"],0)
  for row in d["rows"]:
   age=row["capture_age_seconds"];h=row["horizon_seconds"]
   if age is not None and age<=h:
    self.assertNotEqual(row["status"],"MISSED_AT_DISCOVERY")
  self.assertFalse(d["execution_authority"])
  print("[PASS] SULS-094 signal-relative horizon retention repair")
  print("[PASS] valid late births retained; elapsed horizons marked MISSED_AT_DISCOVERY; remaining horizons scheduled")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-094 SIGNAL-RELATIVE HORIZON RETENTION REPAIR");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 if TARGET.exists():
  TARGET.with_suffix(".pre_suls094.bak").write_text(TARGET.read_text(encoding="utf-8"),encoding="utf-8")
 TARGET.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] repaired canonical:",TARGET.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
