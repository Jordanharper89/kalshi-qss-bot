from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_oracle_sports_full_cycle_gate import run_gate

r=run_gate(Path.cwd())
print("[RESULT]",r)
assert r["launcher_process_alive"] is True
assert r["oracle_reported_sports_healthy"] is True
assert r["all_six_leagues_seen"] is True
assert r["sports_heartbeat_advanced"] is True
assert r["sports_cycles_end"] >= r["sports_cycles_start"] + 1
assert r["sports_restarts"] == 0
assert r["wrapper_used"] is False
assert r["execution_authority"] is False
print("[PASS] real run_oracle_LIVE.py remained alive")
print("[PASS] Oracle reported native sports=HEALTHY")
print("[PASS] all six admitted leagues completed durable runtime rows")
print("[PASS] sports child heartbeat advanced after full six-league cycle")
print("[PASS] sports_restarts=0")
print("[PASS] wrapper not used")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-095 full-cycle physical repair certified")
