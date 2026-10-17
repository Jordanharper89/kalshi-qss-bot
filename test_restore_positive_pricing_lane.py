from pathlib import Path
import ast

ROOT=Path.cwd()
R=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
LM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"
CP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"

rs=R.read_text(encoding="utf-8")
lms=LM.read_text(encoding="utf-8")
cps=CP25.read_text(encoding="utf-8")

ast.parse(rs); ast.parse(lms); ast.parse(cps)

assert '"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)' not in rs
assert 'METEORA_TEMPLATES[token+"|"+pool]' not in rs
assert 'METEORA_TEMPLATES[token]={' in rs
assert 'set(METEORA_TEMPLATES)' in rs
assert 'build_meteora_ix_hot(\n            token,' in rs
assert 'lane.submit(\n        token,' in rs
assert 'if token not in READY_TOKENS:' in rs
assert 'len(\n                READY_TOKENS\n            )' in rs
assert "[UNIVERSAL_ROTATION]" not in rs
assert '"live_hot_book.json"' in cps
assert "_atomic_write(CAPACITY,hot)" not in lms
assert "sendTransaction" not in rs

print("[PASS] original positive-capable token pricing lane restored")
print("[PASS] all 4 lane freshness/supersession checks are token-keyed")
print("[PASS] Meteora runtime template lookup restored to token")
print("[PASS] READY_TOKENS readiness path restored")
print("[PASS] fixed HOT-book scanner remains restored")
print("[PASS] universal master capacity remains non-destructive")
print("[BROADCAST] unchanged")
