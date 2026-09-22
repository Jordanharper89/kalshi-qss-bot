
from qseries_v2.oracle_source_network.certification.remaining_sports_surface_runner import run,REPORT
r=run()
print("[REPORT]",{"passed":r["passed"],"rows":[(x["league"],x["kind"],x["passed"]) for x in r["rows"]],"execution_authority":r["execution_authority"]})
assert all(x["passed"] for x in r["rows"]), "one or more remaining sports production surfaces failed physical certification"
assert r["execution_authority"] is False
assert REPORT.exists()
print("[PASS] OSN-054 remaining sports surface physical runner certified")
