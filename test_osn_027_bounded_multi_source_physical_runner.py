
import subprocess
import sys

probe = """
from qseries_v2.oracle_source_network.certification.sports_physical_runner import run_certified_sources
results=run_certified_sources(max_workers=4)
for r in results:
    print(f"[SOURCE] {r.league} passed={r.passed} rc={r.returncode}")
    if not r.passed:
        print(r.output_tail)
assert len(results)==7
assert all(r.passed for r in results)
assert all(r.execution_authority is False for r in results)
print("[PASS] seven admitted sports sources physically re-certified")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=55)
except subprocess.TimeoutExpired:
    raise AssertionError("multi-source physical runner exceeded hard 55-second gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"multi-source physical runner failed rc={p.returncode}"
print("[PASS] OSN-027 bounded multi-source physical runner certified")
