
from qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v3_REPAIR import admission

r=admission()
print("[ADMISSION_V3_REPAIR]",r)

assert r["passed"] is True
assert r["admitted"]==("NFL","NCAAF","NBA","NHL","MLS","EPL")
assert r["held"]==("NCAAB",)
assert r["blocked"]==("UCL",)
assert r["execution_authority"] is False

print("[PASS] NFL/NCAAF/NBA/NHL/MLS/EPL production event extraction admitted")
print("[PASS] NCAAB held only for current offseason-empty live page")
print("[PASS] UCL remains blocked")
print("[PASS] OSN-055 repaired sports production admission gate certified")
