from pathlib import Path
import py_compile

R=Path.cwd()
M51=R/"qseries_v2/oracle_predictive_discovery/opd_051_exact_witnessed_future_path_outcome.py"
M56=R/"qseries_v2/oracle_predictive_discovery/opd_056_highwater_witnessed_future_outcome.py"
T=R/"test_opd_066_EXACT_ANCHOR_SEQUENCE_SPARSE_5S_REPAIR.py"

M51.write_text(r"""from qseries_v2.oracle_predictive_discovery.opd_050_exact_horizon_coverage_witness import read_path_and_witness
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def materialize_from_path_and_witness(state,path,witness):
 t0=float(state["observed_epoch"]);end=t0+int(state["horizon_seconds"]);p0=float(state["anchor_price"])
 if witness is None or float(witness["event_epoch"])<end:return None
 future=[x for x in path if x["ticker"]==state["ticker"] and t0<float(x["event_epoch"])<=end]
 if not future:
  return {"state_id":state["state_id"],"resolution_epoch":end,"future_return":0.0,"mfe":0.0,"mae":0.0,
  "hit_plus_05":False,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False,
  "future_end_price":p0,"time_to_max_seconds":0.0,"time_to_min_seconds":0.0,
  "coverage_witness_epoch":float(witness["event_epoch"]),"outcome_basis":"CARRY_FORWARD_NO_SAME_TICKER_EVENT_BEFORE_HORIZON"}
 future.sort(key=lambda x:(x["event_epoch"],x.get("sequence_number",0)))
 pend=float(future[-1]["price"]);mx=max(future,key=lambda x:float(x["price"]));mn=min(future,key=lambda x:float(x["price"]))
 mfe=float(mx["price"])-p0;mae=float(mn["price"])-p0
 return {"state_id":state["state_id"],"resolution_epoch":end,"future_return":pend-p0,"mfe":mfe,"mae":mae,
 "hit_plus_05":mfe>=.05,"hit_minus_05":mae<=-.05,"hit_plus_10":mfe>=.10,"hit_minus_10":mae<=-.10,
 "future_end_price":pend,"time_to_max_seconds":float(mx["event_epoch"])-t0,"time_to_min_seconds":float(mn["event_epoch"])-t0,
 "coverage_witness_epoch":float(witness["event_epoch"]),"outcome_basis":"OBSERVED_SAME_TICKER_PATH"}

def materialize_live(state,root=None,guard_seconds=30.0):
 end=float(state["observed_epoch"])+int(state["horizon_seconds"])
 path,witness=read_path_and_witness(state["ticker"],state["observed_epoch"],end,root,guard_seconds)
 return materialize_from_path_and_witness(state,path,witness)
""",encoding="utf-8")

M56.write_text(r"""from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_055_event_time_highwater_coverage import read_until_witness
from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import SOURCE
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def exact_anchor_sequence(state,root=None):
 aid=str(state.get("anchor_id") or "").strip()
 if not aid:return None
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY")
   q.execute("SET LOCAL statement_timeout='5000ms'")
   q.execute("SELECT sequence_number FROM public.oracle_canonical_observations WHERE source_id=%s AND observation_id=%s ORDER BY sequence_number DESC LIMIT 1",(SOURCE,aid))
   row=q.fetchone()
  c.rollback()
 return int(row[0]) if row else None

def materialize_live(state,root=None,after_sequence=None):
 start=exact_anchor_sequence(state,root) if after_sequence is None else int(after_sequence)
 if start is None:return None
 end=float(state["observed_epoch"])+int(state["horizon_seconds"])
 path,witness,highwater=read_until_witness(state["ticker"],state["observed_epoch"],end,root,start,2000,16)
 out=materialize_from_path_and_witness(state,path,witness)
 if out is not None:
  out["coverage_start_sequence"]=int(start)
  out["coverage_highwater_sequence"]=int(highwater)
  out["anchor_sequence_exact"]=True
 return out
""",encoding="utf-8")

T.write_text(r"""from pathlib import Path
import json,time
from unittest.mock import patch
import qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome as m51
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m56
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact

s={"state_id":"DET","anchor_id":"obs-anchor","ticker":"KXTEST","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.50}
w={"ticker":"KXTEST","event_epoch":106.0,"price":.50,"sequence_number":12}
z=m51.materialize_from_path_and_witness(s,[],w)
assert z["future_return"]==0.0 and z["mfe"]==0.0 and z["mae"]==0.0
assert z["future_end_price"]==.50 and z["outcome_basis"].startswith("CARRY_FORWARD")
p=[{"ticker":"KXTEST","event_epoch":101.0,"price":.52,"sequence_number":10},{"ticker":"KXTEST","event_epoch":104.0,"price":.57,"sequence_number":11}]
x=m51.materialize_from_path_and_witness(s,p,w)
assert round(x["future_return"],8)==.07 and x["outcome_basis"]=="OBSERVED_SAME_TICKER_PATH"
with patch.object(m56,"exact_anchor_sequence",lambda *a,**k:9),patch.object(m56,"read_until_witness",lambda *a,**k:([],w,12)):
 y=m56.materialize_live(s,".")
 assert y["coverage_start_sequence"]==9 and y["anchor_sequence_exact"] is True and y["future_return"]==0.0
print("[DETERMINISTIC] observed-path preserved; sparse carry-forward certified")

root=Path.cwd();rt=root/"runtime"/"predictive_data"
def rows(p):return [json.loads(v) for v in p.read_text(encoding="utf-8").splitlines() if v.strip()] if p.exists() else []
done={v["state_id"] for v in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
states=[v for v in rows(rt/"opd_032_prospective_state_ledger.jsonl")
 if int(v.get("horizon_seconds",-1))==5 and v["state_id"] not in done and time.time()>=float(v["observed_epoch"])+5]
assert states,"NO_MATURE_UNRESOLVED_LIVE_5S_STATES"
winner=None
for st in reversed(states[-24:]):
 seq=m56.exact_anchor_sequence(st,root)
 if seq is None:
  print("[SKIP_NO_ANCHOR_SEQUENCE]",st["state_id"][:12],st["ticker"]);continue
 out=m56.materialize_live(st,root)
 print("[TRY]",st["state_id"][:12],st["ticker"],"[ANCHOR_SEQ]",seq,"[RESULT]",out is not None)
 if out is not None:
  winner=(st,out);break
assert winner,"NO_WITNESSED_LIVE_5S_STATE_FOUND_IN_24_RECENT_STATES"
st,out=winner
resolve_exact(out,root)
r={v["state_id"]:v for v in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}[st["state_id"]]
assert r["strictly_future"] is True
assert float(r["resolution_epoch"])>=float(st["observed_epoch"])+5
print("[STATE_ID]",st["state_id"])
print("[TICKER]",st["ticker"])
print("[OUTCOME_BASIS]",out["outcome_basis"])
print("[ANCHOR_SEQUENCE]",out["coverage_start_sequence"])
print("[HIGHWATER_SEQUENCE]",out["coverage_highwater_sequence"])
print("[FUTURE_RETURN]",out["future_return"],"[MFE]",out["mfe"],"[MAE]",out["mae"])
print("[STRICTLY_FUTURE]",r["strictly_future"])
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] exact-anchor-sequence sparse 5-second prospective outcome physically certified")
""",encoding="utf-8")

for p in (M51,M56,T):
 py_compile.compile(str(p),doraise=True)
print("[PASS] foundational OPD-051/056 exact-anchor sparse-horizon repair installed")
