from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_055_event_time_highwater_coverage.py";T=R/"test_opd_055_event_time_highwater_coverage_V1.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
execution_authority=False
SQL="SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number>%s ORDER BY sequence_number ASC LIMIT %s"
def read_until_witness(ticker,t0,end,root=None,after_sequence=0,batch_size=2000,max_batches=8):
 root=Path(root or Path.cwd());seq=int(after_sequence);path=[];witness=None
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
   for _ in range(int(max_batches)):
    q.execute(SQL,(SOURCE,seq,int(batch_size)));rows=q.fetchall() or []
    if not rows:break
    for sn,outer,obj in rows:
     seq=max(seq,int(sn));oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
     if not p or p["ticker"]!=ticker:continue
     ep=float(p["event_epoch"])
     if float(t0)<ep<=float(end):path.append(dict(p,sequence_number=int(sn)))
     if ep>=float(end):witness=dict(p,sequence_number=int(sn));break
    if witness:break
  c.rollback()
 path.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
 return path,witness,seq
""",encoding="utf-8")
T.write_text("""from unittest.mock import patch
from datetime import datetime,timezone
import qseries_v2.oracle_predictive_discovery.opd_055_event_time_highwater_coverage as m
def obj(t,p):return {"payload":{"source_market_id":"KXTEST","message":{"market_ticker":"KXTEST","ts":t,"yes_price_dollars":p}}}
class Q:
 def __init__(self):self.n=0
 def execute(self,*a):pass
 def fetchall(self):
  self.n+=1
  return [(10,datetime.fromtimestamp(180,tz=timezone.utc),obj(101,.51)),(11,datetime.fromtimestamp(181,tz=timezone.utc),obj(104,.53))] if self.n==1 else [(12,datetime.fromtimestamp(250,tz=timezone.utc),obj(106,.54))]
 def __enter__(self):return self
 def __exit__(self,*a):pass
class C:
 def __init__(self):self.q=Q()
 def cursor(self):return self.q
 def rollback(self):pass
 def __enter__(self):return self
 def __exit__(self,*a):pass
with patch.object(m,"connect",lambda *a,**k:C()):
 p,w,s=m.read_until_witness("KXTEST",100,105,".",0,2000,8)
 assert [x["event_epoch"] for x in p]==[101.0,104.0] and w["event_epoch"]==106.0 and s==12
print("[PATH_POINTS]",len(p),"[WITNESS]",w["event_epoch"],"[HIGHWATER]",s)
print("[PASS] OPD-055 event-time/highwater coverage certified independent of storage lag")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-055 V1 installed")