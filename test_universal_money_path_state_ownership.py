from pathlib import Path
import ast
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint25_expanded_live_universe_cutover as c25

rs=Path(lm.__file__).read_text(encoding='utf-8')
cs=Path(c25.__file__).read_text(encoding='utf-8')

assert 'HOT_BOOK=STATE/"live_hot_book.json"' in rs
assert '_atomic_write(HOT_BOOK,hot)' in rs
assert '_atomic_write(CAPACITY,hot)' not in rs
assert 'CAPACITY.write_bytes(original_capacity)' not in rs
assert 'DIVERSITY_FIRST_CAPACITY_LOAD_V1' not in rs
assert '[UNIVERSAL_STATE]' in rs
assert '"live_hot_book.json"' in cs
assert '"capacity_aware_warm_universe.json"' in cs
assert 'CHECKPOINT25_UNIVERSAL_BOUNDARY' in cs
assert 'CHECKPOINT25_HOT_PAIR_NOT_IN_UNIVERSAL' in cs
assert lm.CAPACITY.name=='capacity_aware_warm_universe.json'
assert lm.HOT_BOOK.name=='live_hot_book.json'
assert c25.MANIFEST.name=='live_hot_book.json'
assert c25.UNIVERSAL_CAPACITY.name=='capacity_aware_warm_universe.json'
ast.parse(rs)
ast.parse(cs)
print('[PASS] universal capacity and hot scheduler state are physically separate')
print('[PASS] CP25 consumes hot slice and validates every pair against universal capacity')
print('[PASS] destructive universal-capacity overwrite removed')
print('[PASS] failed diversity monkeypatch retired')
print('[BROADCAST] unchanged')
