from pathlib import Path

p=Path("qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence")
p.mkdir(parents=True,exist_ok=True)

m=p/"ooi_006_slop_universal_opportunity_materializer.py"
m.write_text(r'''from qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity import UniversalOpportunity

REVISION="OOI_006_SLOP_UNIVERSAL_OPPORTUNITY_MATERIALIZER"
EXECUTION_AUTHORITY=False

def materialize_slop(op):
    conditions=dict(op.conditions or {})
    return UniversalOpportunity(
        opportunity_id=str(op.prediction_id),
        market_id=str(op.pair_address),
        market_type="SOLANA",
        venue_id="SOLANA",
        venue_name="Solana",
        opportunity_type="BUY_PRESSURE",
        direction="BUY",
        expected_value=0.0,
        expected_edge=0.0,
        confidence=0.0,
        explanation="Prospective SLOP BUY_PRESSURE opportunity",
        supporting_prediction_ids=[str(op.prediction_id)],
        tags=["SLOP","BUY_PRESSURE","PROSPECTIVE"],
        raw_market={"token_address":str(op.token_address),
                    "pair_address":str(op.pair_address)},
        metadata={"source_revision":"SLOP_078B",
                  "frozen_at":str(op.frozen_at),
                  "conditions":conditions,
                  "horizon_seconds":op.horizon_seconds,
                  "target":op.target,
                  "stop":op.stop,
                  "friction_bps":op.friction_bps,
                  "execution_authority":False},
        read_only=True)
''',encoding="utf-8")

t=Path("test_ooi_006_slop_universal_opportunity_materializer.py")
t.write_text(r'''from types import SimpleNamespace
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
''',encoding="utf-8")

print("[PASS] OOI-006 installed")
print("[NEXT] run deterministic UniversalOpportunity materialization certification")