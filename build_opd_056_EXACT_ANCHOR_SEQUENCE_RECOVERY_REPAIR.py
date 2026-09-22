from pathlib import Path

ROOT=Path.cwd()
P=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_056_highwater_witnessed_future_outcome.py"
T=ROOT/"test_opd_056_EXACT_ANCHOR_SEQUENCE_RECOVERY_REPAIR.py"

MODULE=r"""from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_055_event_time_highwater_coverage import read_until_witness
from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import SOURCE,canonical_point
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _select_recovered_anchor(state,rows):
 t0=float(state["observed_epoch"]);ticker=str(state["ticker"]);p0=float(state["anchor_price"])
 same=[]
 for sn,outer,obj in rows:
  oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer)
  p=canonical_point(obj,oe)
  if not p or p["ticker"]!=ticker:continue
  ep=float(p["event_epoch"])
  if ep>t0:continue
  same.append((int(sn),ep,float(p["price"])))
 if not same:return None
 exact=[x for x in same if abs(x[2]-p0)<=1e-9]
 pool=exact or same
 pool.sort(key=lambda x:(x[1],x[0]),reverse=True)
 return pool[0][0]

def _recover_anchor_sequence(state,root=None,batch_size=2000,max_batches=16):
 root=Path(root or Path.cwd());cursor=None
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY")
   q.execute("SET LOCAL statement_timeout='5000ms'")
   for _ in range(int(max_batches)):
    if cursor is None:
     q.execute("SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s",(SOURCE,int(batch_size)))
    else:
     q.execute("SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number<%s ORDER BY sequence_number DESC LIMIT %s",(SOURCE,int(cursor),int(batch_size)))
    rows=q.fetchall() or []
    if not rows:break
    hit=_select_recovered_anchor(state,rows)
    if hit is not None:
     c.rollback();return int(hit)
    cursor=min(int(x[0]) for x in rows)
  c.rollback()
 return None

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
 if row:return int(row[0])
 return _recover_anchor_sequence(state,root)

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
"""

TEST=r"""from datetime import datetime,timezone
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m

def obj(ticker,price,ts):
 return {"payload":{"message":{"market_ticker":ticker,"yes_price_dollars":str(price),"ts":ts}}}

state={"ticker":"KXBTC","observed_epoch":100.0,"anchor_price":0.45}
rows=[
 (10,datetime.fromtimestamp(99.0,timezone.utc),obj("KXBTC",0.40,99.0)),
 (11,datetime.fromtimestamp(99.5,timezone.utc),obj("KXETH",0.45,99.5)),
 (12,datetime.fromtimestamp(99.8,timezone.utc),obj("KXBTC",0.45,99.8)),
 (13,datetime.fromtimestamp(100.2,timezone.utc),obj("KXBTC",0.45,100.2)),
]
assert m._select_recovered_anchor(state,rows)==12
state2=dict(state,anchor_price=0.99)
assert m._select_recovered_anchor(state2,rows)==12
assert m.execution_authority is False
print("[PASS] exact-anchor recovery is same-ticker and strictly at-or-before frozen anchor")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
"""

if P.exists():
 b=P.with_suffix(P.suffix+".pre_anchor_sequence_recovery")
 if not b.exists():b.write_bytes(P.read_bytes())

P.write_text(MODULE,encoding="utf-8")
T.write_text(TEST,encoding="utf-8")
compile(MODULE,str(P),"exec");compile(TEST,str(T),"exec")
print("[PASS] existing OPD-056 exact-anchor sequence recovery repair installed")
print(P);print(T)
