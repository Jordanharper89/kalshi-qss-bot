from pathlib import Path
import ast
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

ROOT=Path.cwd()
R=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
LM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"
CP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"

rs=R.read_text(encoding="utf-8")
lms=LM.read_text(encoding="utf-8")
cps=CP25.read_text(encoding="utf-8")
ast.parse(rs); ast.parse(lms); ast.parse(cps)

assert "async def serve_canonical(" in rs
assert "[CANONICAL_WS]" in rs
assert "[UNIVERSAL_ROTATION]" not in rs
assert "[UNIVERSAL_SURVEILLANCE]" not in rs
assert "def build_universal_subscription_windows" not in rs
assert '"live_hot_book.json"' in cps
assert 'print("[FEED_FREEZE] true",flush=True)' in lms
assert "_atomic_write(CAPACITY,hot)" not in lms
assert '"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)' in rs
assert 'METEORA_TEMPLATES[token+"|"+pool]' in rs
assert "sendTransaction" not in rs

print("[PASS] fixed HOT-book canonical scanner restored")
print("[PASS] universal rotation path removed")
print("[PASS] CP25 consumes live_hot_book again")
print("[PASS] exact-pair identity preserved")
print("[PASS] universal capacity remains non-destructively preserved")
print("[PASS] broadcast remains disabled")
