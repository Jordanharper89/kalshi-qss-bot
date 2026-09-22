from pathlib import Path
MODULE=r"""from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_055_event_time_highwater_coverage import read_until_witness
from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def state_time_highwater(root,observed_epoch):
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as conn:
  with conn.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY")
   cur.execute("SET LOCAL statement_timeout='5000ms'")
   cur.execute("SELECT sequence_number FROM public.oracle_canonical_observations WHERE observed_at<=to_timestamp(%s) ORDER BY sequence_number DESC LIMIT 1",(float(observed_epoch),))
   row=cur.fetchone()
  conn.rollback()
 return int(row[0]) if row else 0

def materialize_live(state,root=None,after_sequence=None):
 root=Path(root or Path.cwd())
 start=state_time_highwater(root,state["observed_epoch"]) if after_sequence is None else int(after_sequence)
 end=float(state["observed_epoch"])+int(state["horizon_seconds"])
 path,witness,highwater=read_until_witness(state["ticker"],state["observed_epoch"],end,root,start)
 out=materialize_from_path_and_witness(state,path,witness)
 if out is not None:
  out["coverage_start_sequence"]=int(start)
  out["coverage_highwater_sequence"]=int(highwater)
 return out
"""
TEST=r"""from pathlib import Path
import json
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m
root=Path.cwd();rt=root/"runtime"/"predictive_data"

capt={}
m.state_time_highwater=lambda root,t:123
m.read_until_witness=lambda ticker,start,end,root,after:(capt.update({"after":after}) or ([{"event_epoch":106.0,"price":0.57}],106.0,140))
m.materialize_from_path_and_witness=lambda state,path,witness:{"state_id":state["state_id"],"resolution_epoch":witness}
r=m.materialize_live({"state_id":"x","ticker":"KXBTC-X","observed_epoch":100.0,"horizon_seconds":5},root)
assert capt["after"]==123 and r["coverage_start_sequence"]==123 and r["coverage_highwater_sequence"]==140

from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import cycle
sp=rt/"opd_061_live_anchor_spool.jsonl";st=rt/"opd_032_prospective_state_ledger.jsonl";ou=rt/"opd_033_prospective_outcome_ledger.jsonl"
def rows(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
anchors={x["anchor_id"]:x for x in rows(sp)}
before={x["state_id"] for x in rows(ou)}
live5=[x for x in rows(st) if int(x.get("horizon_seconds",-1))==5 and x.get("anchor_id") in anchors and x["state_id"] not in before]
assert live5,"NO_UNRESOLVED_LIVE_5S_STATES"
import importlib
wm=importlib.reload(__import__("qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker",fromlist=["cycle"]))
result=wm.cycle(root)
after=rows(ou)
new=[x for x in after if x.get("state_id") not in before and x.get("strictly_future") is True]
live_ids={x["state_id"] for x in live5}
new5=[x for x in new if x.get("state_id") in live_ids]
print("[WORKER_CYCLE]",result)
print("[NEW_STRICTLY_FUTURE_OUTCOMES]",len(new))
print("[NEW_LIVE_5S_OUTCOMES]",len(new5))
assert new5,"HIGHWATER_REPAIR_RAN_BUT_NO_LIVE_5S_STATE_RESOLVED"
print("[STATE_ID]",new5[0]["state_id"],"[RESOLUTION_EPOCH]",new5[0]["resolution_epoch"])
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-066 highwater repair physically resolved live 5-second prospective state")
"""
root=Path.cwd()
m=root/"qseries_v2/oracle_predictive_discovery/opd_056_highwater_witnessed_future_outcome.py"
m.write_text(MODULE,encoding="utf-8")
(root/"test_opd_066_state_time_highwater_outcome_REPAIR_V6.py").write_text(TEST,encoding="utf-8")
import py_compile
py_compile.compile(str(m),doraise=True)
py_compile.compile(str(root/"test_opd_066_state_time_highwater_outcome_REPAIR_V6.py"),doraise=True)
print("[PASS] OPD-066 REPAIR V6 installed")
