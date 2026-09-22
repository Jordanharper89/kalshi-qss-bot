
from qseries_v2.oracle_source_network.certification.universal_sports_event_runner import run,REPORT
r=run()
print("[UNIVERSAL_REPORT]",{
    "physical_reruns":[(x["league"],x["passed"]) for x in r["physical_reruns"]],
    "nba_certified_admission":r["nba_certified_admission"],
    "passed":r["passed"],
})
assert r["passed"] is True
assert len(r["physical_reruns"])==5
assert all(x["passed"] for x in r["physical_reruns"])
assert r["nba_certified_admission"] is True
assert r["execution_authority"] is False
assert REPORT.exists()
print("[PASS] five exact physical source tests re-run + NBA certified admission retained")
print("[PASS] OSN-059 universal sports event runner certified")
