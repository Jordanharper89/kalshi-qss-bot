from unittest.mock import patch
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
