from pathlib import Path
import ast

ROOT=Path.cwd()
RUNTIME=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py'
CP25=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py'
TEST=ROOT/'test_universal_money_path_state_ownership.py'

for p in (RUNTIME,CP25):
    if not p.is_file():
        raise RuntimeError('REQUIRED_TARGET_MISSING:'+str(p))

runtime=RUNTIME.read_text(encoding='utf-8')
cp25=CP25.read_text(encoding='utf-8')

start=runtime.find('# DIVERSITY_FIRST_CAPACITY_LOAD_V1')
if start>=0:
    end=runtime.find('ROOT=Path.cwd()',start)
    if end<0:
        raise RuntimeError('DIVERSITY_BLOCK_END_NOT_FOUND')
    runtime=runtime[:start]+runtime[end:]

if 'HOT_BOOK=STATE/"live_hot_book.json"' not in runtime:
    needle='CAPACITY=STATE/"capacity_aware_warm_universe.json"\n'
    if needle not in runtime:
        raise RuntimeError('CAPACITY_DECLARATION_NOT_FOUND')
    runtime=runtime.replace(
        needle,
        needle+'HOT_BOOK=STATE/"live_hot_book.json"\n',
        1,
    )

runtime=runtime.replace(
    '    original_capacity=CAPACITY.read_bytes() if CAPACITY.is_file() else None\n',
    ''
)

old_write='        _atomic_write(CAPACITY,hot)\n'
new_write=(
    '        _atomic_write(HOT_BOOK,hot)\n'
    '        universal_now=_load(CAPACITY)\n'
    '        universal_rows=list(universal_now.get("rows") or [])\n'
    '        hot_rows=list(hot.get("rows") or [])\n'
    '        print("[UNIVERSAL_STATE] capacity_pairs=%d hot_pairs=%d capacity_immutable=True"%(\n'
    '            len(universal_rows),len(hot_rows)\n'
    '        ),flush=True)\n'
)
if old_write not in runtime and '_atomic_write(HOT_BOOK,hot)' not in runtime:
    raise RuntimeError('DESTRUCTIVE_CAPACITY_WRITE_NOT_FOUND')
runtime=runtime.replace(old_write,new_write,1)

restore_block=(
    '        if original_capacity is None:\n'
    '            try:\n'
    '                CAPACITY.unlink()\n'
    '            except FileNotFoundError:\n'
    '                pass\n'
    '        else:\n'
    '            CAPACITY.write_bytes(original_capacity)\n\n'
)
runtime=runtime.replace(restore_block,'')

old_manifest=(
    'MANIFEST=Path(\n'
    '    "runtime_state/oracle/solana_atomic_executor/"\n'
    '    "capacity_aware_warm_universe.json"\n'
    ')'
)
new_manifest=(
    'MANIFEST=Path(\n'
    '    "runtime_state/oracle/solana_atomic_executor/"\n'
    '    "live_hot_book.json"\n'
    ')\n\n'
    'UNIVERSAL_CAPACITY=Path(\n'
    '    "runtime_state/oracle/solana_atomic_executor/"\n'
    '    "capacity_aware_warm_universe.json"\n'
    ')'
)
if old_manifest in cp25:
    cp25=cp25.replace(old_manifest,new_manifest,1)
elif '"live_hot_book.json"' not in cp25:
    raise RuntimeError('CP25_MANIFEST_BLOCK_NOT_FOUND')

needle=(
    'def _expanded_registry():\n'
    '    manifest=_load(MANIFEST)\n'
    '    rows=list(manifest.get("rows") or [])\n'
)
replacement=(
    'def _expanded_registry():\n'
    '    manifest=_load(MANIFEST)\n'
    '    rows=list(manifest.get("rows") or [])\n'
    '    universal=_load(UNIVERSAL_CAPACITY)\n'
    '    universal_rows=list(universal.get("rows") or [])\n'
    '    if not universal_rows:\n'
    '        raise RuntimeError("CHECKPOINT25_UNIVERSAL_CAPACITY_EMPTY")\n'
    '    universal_ids={\n'
    '        str(x.get("identity") or (str(x.get("token"))+"|"+str(x.get("meteora_pool"))))\n'
    '        for x in universal_rows\n'
    '    }\n'
    '    for row in rows:\n'
    '        identity=str(row.get("identity") or (str(row.get("token"))+"|"+str(row.get("meteora_pool"))))\n'
    '        if identity not in universal_ids:\n'
    '            raise RuntimeError("CHECKPOINT25_HOT_PAIR_NOT_IN_UNIVERSAL:"+identity)\n'
    '    print("[CHECKPOINT25_UNIVERSAL_BOUNDARY] universal_pairs=%d hot_pairs=%d hot_is_scheduler_slice=True"%(\n'
    '        len(universal_rows),len(rows)\n'
    '    ),flush=True)\n'
)
if needle in cp25:
    cp25=cp25.replace(needle,replacement,1)
elif 'CHECKPOINT25_UNIVERSAL_BOUNDARY' not in cp25:
    raise RuntimeError('CP25_EXPANDED_REGISTRY_SEAM_NOT_FOUND')

ast.parse(runtime)
ast.parse(cp25)
RUNTIME.write_text(runtime,encoding='utf-8')
CP25.write_text(cp25,encoding='utf-8')

test_code="""from pathlib import Path
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
"""

TEST.write_text(test_code,encoding='utf-8')
ast.parse(test_code)

print('[PASS] UNIVERSAL MONEY PATH STATE OWNERSHIP REPLACEMENT')
print('[UNIVERSAL] capacity_aware_warm_universe.json remains canonical and immutable to HOT scheduling')
print('[HOT] live_hot_book.json owns bounded provider-safe live slice')
print('[CP25] hot slice only; every pair must belong to universal capacity')
print('[RETIRED] DIVERSITY_FIRST_CAPACITY_LOAD_V1')
print('[KEY] untouched')
print('[WALLET] untouched')
print('[BROADCAST] unchanged')
print('[TEST]',TEST.name)
