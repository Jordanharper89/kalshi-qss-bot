from pathlib import Path
import ast
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm

s=Path(r.__file__).read_text(encoding="utf-8")
o=Path(lm.__file__).read_text(encoding="utf-8")
ast.parse(s)
ast.parse(o)

assert '"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)' in s
assert 'METEORA_TEMPLATES[token+"|"+pool]' in s
assert 'pair_key=token+"|"+str(snap["meteora"]["address"])' in s
assert 'build_meteora_ix_hot(\n            pair_key,' in s
assert 'pair_key=str(snap["pair_key"])' in s
assert 'lane.submit(\n        pair_key,' in s
assert '_atomic_write(CAPACITY,hot)' not in o
assert 'live_hot_book.json' in o
assert 'sendTransaction' not in s

class P:
    token="TOKEN_A"
    meteora_pool="POOL_1"
    pump_pool="PUMP"
    token_x="TOKEN_A"
    token_y="WSOL"
    decimals_x=6
    decimals_y=9
    dlmm_state={}
    pump_base_reserve=1
    pump_quote_reserve=1

p=P()
a=r.immutable_snapshot(p)
p.meteora_pool="POOL_2"
b=r.immutable_snapshot(p)
assert a["pair_key"]=="TOKEN_A|POOL_1"
assert b["pair_key"]=="TOKEN_A|POOL_2"
assert a["pair_key"]!=b["pair_key"]

print("[PASS] literal exact-pair identity replacement")
print("[PASS] same-token alternate Meteora pools remain distinct")
print("[PASS] lane/freshness/template identity=token|meteora_pool")
print("[PASS] universal/HOT ownership preserved")
print("[BROADCAST] unchanged")
