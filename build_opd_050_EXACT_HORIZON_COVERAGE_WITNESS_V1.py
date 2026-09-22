from pathlib import Path
import py_compile
R=Path.cwd()
M=R/"qseries_v2/oracle_predictive_discovery/opd_050_exact_horizon_coverage_witness.py"
T=R/"test_opd_050_exact_horizon_coverage_witness_V1.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
execution_authority=False
SQL="SELECT sequence_number, observed_at, canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND observed_at >= to_timestamp(%s) AND observed_at <= to_timestamp(%s) ORDER BY sequence_number ASC"
def read_path_and_witness(ticker,t0,end,root=None,guard_seconds=30.0):
 root=Path(root or Path.cwd());hi=float(end)+max(1.0,float(guard_seconds))
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
   q.execute(SQL,(SOURCE,float(t0),hi));raw=q.fetchall() or []
  c.rollback()
 points=[]
 for seq,outer,obj in raw:
  oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
  if p and p["ticker"]==ticker and p["event_epoch"]>float(t0):points.append(dict(p,sequence_number=int(seq)))
 points.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
 path=[x for x in points if x["event_epoch"]<=float(end)]
 witness=next((x for x in points if x["event_epoch"]>=float(end)),None)
 return path,witness
""",encoding="utf-8")
T.write_text("""from unittest.mock import patch
from datetime import datetime,timezone
import qseries_v2.oracle_predictive_discovery.opd_050_exact_horizon_coverage_witness as m
class Q:
 def execute(self,*a):pass
 def fetchall(self):
  def o(t,p):return {"payload":{"source_market_id":"KXTEST","message":{"market_ticker":"KXTEST","ts":t,"yes_price_dollars":p}}}
  return [(1,datetime.fromtimestamp(101,tz=timezone.utc),o(101,.51)),(2,datetime.fromtimestamp(104,tz=timezone.utc),o(104,.53)),(3,datetime.fromtimestamp(106,tz=timezone.utc),o(106,.54))]
 def __enter__(self):return self
 def __exit__(self,*a):pass
class C:
 def cursor(self):return Q()
 def rollback(self):pass
 def __enter__(self):return self
 def __exit__(self,*a):pass
with patch.object(m,"connect",lambda *a,**k:C()):
 path,w=m.read_path_and_witness("KXTEST",100,105,".",30)
 assert [x["event_epoch"] for x in path]==[101.0,104.0]
 assert w["event_epoch"]==106.0
print("[PATH_POINTS]",len(path));print("[WITNESS_EPOCH]",w["event_epoch"])
print("[PASS] OPD-050 exact horizon coverage witness certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True)
print("[PASS] OPD-050 V1 installed")