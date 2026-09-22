
import subprocess
import sys

probe = """
from qseries_v2.oracle_source_network.certification.sports_physical_runner import run_certified_sources
from qseries_v2.oracle_source_network.certification.sports_production_readiness import readiness_report
results=run_certified_sources(max_workers=4)
report=readiness_report(results)
print(f"[CERT] {report}")
assert report["passed"]
assert set(report["production_ready_leagues"]) == {"NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL"}
assert report["blocked_leagues"] == ("UCL",)
assert report["execution_authority"] is False
print("[PASS] admitted sports source production-readiness gate certified")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=55)
except subprocess.TimeoutExpired:
    raise AssertionError("sports production-readiness gate exceeded hard 55-second gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"sports production-readiness gate failed rc={p.returncode}"
print("[PASS] OSN-028 sports source production readiness certified")
