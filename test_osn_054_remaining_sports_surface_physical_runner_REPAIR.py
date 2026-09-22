
from qseries_v2.oracle_source_network.certification.remaining_sports_surface_runner_REPAIR import run,REPORT

r=run()
summary=[(x["league"],x["kind"],x["passed"]) for x in r["rows"]]
print("[REPORT]",{"passed":r["passed"],"rows":summary,"execution_authority":r["execution_authority"]})

assert r["passed"] is True
assert all(x["kind"]=="EXTRACTOR" for x in r["rows"])
assert all(x["passed"] for x in r["rows"])
assert {x["league"] for x in r["rows"]}=={"NHL","MLS","EPL"}
assert r["execution_authority"] is False
assert REPORT.exists()

print("[PASS] NHL + MLS + EPL physical extraction all re-certified")
print("[PASS] obsolete failed MLS probe excluded")
print("[PASS] OSN-054 repaired remaining sports physical runner certified")
