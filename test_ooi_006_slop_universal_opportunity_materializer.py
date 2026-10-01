from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop,EXECUTION_AUTHORITY

x=SimpleNamespace(prediction_id="P1",token_address="T1",pair_address="PAIR1",
 frozen_at="2026-09-17T00:00:00Z",conditions={"order_flow":"BUY_PRESSURE"},
 horizon_seconds=60,target=.10,stop=-.05,friction_bps=200)
u=materialize_slop(x)

assert EXECUTION_AUTHORITY is False
assert u.read_only is True
assert u.opportunity_id=="P1"
assert u.market_id=="PAIR1"
assert u.opportunity_type=="BUY_PRESSURE"
assert u.metadata["conditions"]["order_flow"]=="BUY_PRESSURE"
assert u.metadata["horizon_seconds"]==60
assert u.metadata["target"]==.10
assert u.metadata["stop"]==-.05
assert u.metadata["friction_bps"]==200
assert u.supporting_prediction_ids==["P1"]
print("[PASS] SLOP prospective opportunity materializes into existing UniversalOpportunity")
print("[PASS] frozen 60s +10%/-5% 200bps thesis preserved")
print("[PASS] OOI-006 CERTIFIED execution_authority=FALSE")
