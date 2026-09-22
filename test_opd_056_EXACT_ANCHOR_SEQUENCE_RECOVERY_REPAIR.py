from datetime import datetime,timezone
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
