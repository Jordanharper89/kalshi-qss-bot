from pathlib import Path
p=Path("qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence")
m=p/"ooi_007_slop_universal_opportunity_existing_oos_intake.py"
m.write_text('''from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem
from .ooi_006_slop_universal_opportunity_materializer import materialize_slop
REVISION="OOI_007_SLOP_UNIVERSAL_OPPORTUNITY_EXISTING_OOS_INTAKE"
EXECUTION_AUTHORITY=False
def intake_slop(op,system=None):
 u=materialize_slop(op)
 oos=system or OpportunityOperatingSystem()
 result=oos.intake(u)
 return u,result,oos
''',encoding="utf-8")
Path("test_ooi_007_slop_universal_opportunity_existing_oos_intake.py").write_text('''from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007_slop_universal_opportunity_existing_oos_intake import intake_slop,EXECUTION_AUTHORITY
x=SimpleNamespace(prediction_id="P1",token_address="T1",pair_address="PAIR1",
 frozen_at="2026-09-17T00:00:00Z",conditions={"order_flow":"BUY_PRESSURE"},
 horizon_seconds=60,target=.10,stop=-.05,friction_bps=200)
u,r,oos=intake_slop(x)
assert EXECUTION_AUTHORITY is False and u.read_only is True
assert r.opportunity_id=="P1" and r.fingerprint==u.fingerprint()
assert r.registered is not False if hasattr(r,"registered") else True
r2=oos.intake(u)
assert r2.duplicate is True
assert r2.fingerprint==r.fingerprint
assert u.metadata["horizon_seconds"]==60 and u.metadata["target"]==.10
assert u.metadata["stop"]==-.05 and u.metadata["friction_bps"]==200
print("[INTAKE_STATUS]",r.status)
print("[DUPLICATE_STATUS]",r2.status)
print("[FINGERPRINT]",r.fingerprint)
print("[PASS] UniversalOpportunity accepted by existing OOS intake")
print("[PASS] existing OOS fingerprint/deduplication physically proven")
print("[PASS] OOI-007 CERTIFIED execution_authority=FALSE")
''',encoding="utf-8")
print("[PASS] OOI-007 installed")