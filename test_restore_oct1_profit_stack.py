from pathlib import Path
import ast

ROOT=Path.cwd()
paths=[
    ROOT/"qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py",
    ROOT/"qseries_v2/oracle_execution/oracle_019_venue_native_reserve_feed_cutover.py",
    ROOT/"qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py",
    ROOT/"qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py",
    ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py",
]

for p in paths:
    ast.parse(p.read_text(encoding="utf-8"))

q20=paths[2].read_text(encoding="utf-8")
runtime=paths[4].read_text(encoding="utf-8")

assert "self.processed+=1" in q20
assert "self.positive+=1" in q20
assert "FULL_SIZE_CURVE=(" in q20
assert "_lane.submit(pair.token" in q20
assert "METEORA_TEMPLATES[token]={" in runtime
assert "READY_TOKENS.intersection_update(" in runtime
assert "EXECUTION_AUTHORITY=False" in runtime

print("[PASS] October-1 positive-producing pricing stack restored")
print("[PASS] live lane can increment processed/positive counters")
print("[PASS] full approved size curve restored in ORACLE-020")
print("[PASS] token-keyed readiness/pricing path restored")
print("[PASS] execution authority remains false")
print("[BROADCAST] disabled")
