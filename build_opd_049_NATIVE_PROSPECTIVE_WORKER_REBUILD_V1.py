from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py";T=R/"test_opd_049_native_prospective_worker_rebuild_V1.py"
M.write_text("""from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
from qseries_v2.oracle_predictive_discovery.opd_048_exact_future_path_outcome_materializer import materialize_live
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def _write(root,payload):
 p=Path(root)/"runtime"/"predictive_data"/"opd_049_worker_heartbeat.json";p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(".tmp");q.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");q.replace(p)
def cycle(root=None,now=None,materializer=None):
 root=Path(root or Path.cwd());rebuild_exact(root);rows=mature_exact(root,now);resolved=0;abstained=0
 fn=materializer or materialize_live
 for state in rows:
  outcome=fn(state,root)
  if outcome is None:abstained+=1;continue
  resolve_exact(outcome,root);resolved+=1
 return {"mature":len(rows),"resolved":resolved,"abstained":abstained}
def run_forever(root=None,cadence=2.0):
 root=Path(root or Path.cwd()).resolve()
 if cadence<=0:raise ValueError("cadence must be > 0")
 cycles=0
 while True:
  cycles+=1;state="HEALTHY";err=None;result=None
  try:result=cycle(root)
  except Exception as exc:state="DEGRADED";err=f"{type(exc).__name__}: {exc}"
  _write(root,{"schema_version":"OPD-049","cycles":cycles,"state":state,"error":err,"result":result,"execution_authority":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"updated_epoch":time.time()})
  time.sleep(cadence)
""",encoding="utf-8")
T.write_text("""import json,tempfile
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import cycle,execution_authority
with tempfile.TemporaryDirectory() as d:
 r=Path(d);p=r/"runtime"/"predictive_data";p.mkdir(parents=True)
 row={"state_id":"S049","anchor_id":"A049","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"tokens":[],"anchor_price":.50,"matched_family_ids":[],"post_freeze":True}
 (p/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(row)+"\\n")
 def mat(s,root):return {"state_id":s["state_id"],"resolution_epoch":105.0,"future_return":.06,"mfe":.06,"mae":-.03,"hit_plus_05":True,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False}
 x=cycle(r,105.0,mat);assert x=={"mature":1,"resolved":1,"abstained":0}
 out=json.loads((p/"opd_033_prospective_outcome_ledger.jsonl").read_text().splitlines()[0]);assert out["strictly_future"] is True and out["state_id"]=="S049"
 assert execution_authority is False
 print("[MATURE]",x["mature"],"[RESOLVED]",x["resolved"]);print("[STRICTLY_FUTURE]",out["strictly_future"]);print("[PASS] OPD-049 native worker rebuilt on certified 043/044/048 chain")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-049 V1 installed")