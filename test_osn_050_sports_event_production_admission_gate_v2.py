
from qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v2 import production_admission
r=production_admission()
print("[ADMISSION]",r)
assert r["passed"] is True
assert r["admitted"]==("NFL","NCAAF","NBA")
assert set(r["held"])=={"NCAAB","NHL","MLS","EPL"}
assert r["blocked"]==("UCL",)
assert r["execution_authority"] is False
print("[PASS] only physically extracting leagues admitted")
print("[PASS] NCAAB/NHL/MLS/EPL held; UCL blocked")
print("[PASS] OSN-050 production admission gate certified")
