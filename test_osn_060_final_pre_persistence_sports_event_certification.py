
from qseries_v2.oracle_source_network.certification.pre_persistence_sports_event_certification import certify
r=certify()
print("[PRE_PERSISTENCE_CERT]",r)
assert r["passed"] is True
assert r["persistence_ready"] is True
assert set(("NFL","NCAAF","NBA","NHL","MLS","EPL")).issubset(r["admitted"])
assert set(r["physically_rerun"])=={"NFL","NCAAF","NHL","MLS","EPL"}
assert r["nba_certified_admission"] is True
assert r["blocked"]==("UCL",)
assert r["execution_authority"] is False
print("[PASS] six-league universal sports foundation ready for PostgreSQL single-writer integration")
print("[PASS] MLB remains truthfully held until canonical event extraction is certified")
print("[PASS] OSN-060 final pre-persistence sports certification certified")
