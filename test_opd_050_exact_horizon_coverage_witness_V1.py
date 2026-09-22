from unittest.mock import patch
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
