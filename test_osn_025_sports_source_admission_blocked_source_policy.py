
from qseries_v2.oracle_source_network.certification.sports_source_admission import admission_decisions, admitted_leagues

d = admission_decisions()
ucl = [x for x in d if x.league == "UCL"][0]
assert ucl.admitted is False
assert ucl.status == "BLOCKED"
assert "zero bytes" in ucl.reason
assert set(admitted_leagues()) == {"NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL"}
assert all(x.execution_authority is False for x in d)
print("[PASS] admitted_leagues=", admitted_leagues())
print("[PASS] UCL blocked-source exclusion preserved")
print("[PASS] OSN-025 source admission policy certified")
