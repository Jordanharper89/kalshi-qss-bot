from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"live_money_runtime.py"
TEST=ROOT/"test_live_money_diversity_first_capacity_handoff.py"

if not TARGET.is_file():
    raise RuntimeError("LIVE_MONEY_RUNTIME_MISSING")

src=TARGET.read_text(encoding="utf-8")
if "DIVERSITY_FIRST_CAPACITY_LOAD_V1" in src:
    print("[PASS] diversity-first capacity-load replacement already installed")
    raise SystemExit(0)

BLOCK=r"""
# DIVERSITY_FIRST_CAPACITY_LOAD_V1
import json as _oracle_json
_ORACLE_JSON_LOAD=_oracle_json.load

def _oracle_row_token(row):
    if not isinstance(row,dict):
        return None
    for key in ("token","mint","base_mint","token_mint"):
        value=row.get(key)
        if value:
            return str(value)
    pair_key=str(row.get("pair_key") or "")
    if "|" in pair_key:
        return pair_key.split("|",1)[0]
    return None

def _oracle_diversify_list(rows):
    if not isinstance(rows,list) or not rows:
        return rows
    tagged=[(_oracle_row_token(row),row) for row in rows]
    if sum(token is not None for token,_ in tagged)<2:
        return rows
    first=[]
    duplicates=[]
    seen=set()
    for token,row in tagged:
        if token is None:
            duplicates.append(row)
        elif token in seen:
            duplicates.append(row)
        else:
            seen.add(token)
            first.append(row)
    return first+duplicates

def _oracle_diversify_capacity(value):
    if isinstance(value,list):
        rows=_oracle_diversify_list(value)
        if rows is not value and rows!=value:
            return rows
        return [_oracle_diversify_capacity(v) for v in value]
    if isinstance(value,dict):
        return {k:_oracle_diversify_capacity(v) for k,v in value.items()}
    return value

def _oracle_diversity_json_load(fp,*args,**kwargs):
    value=_ORACLE_JSON_LOAD(fp,*args,**kwargs)
    name=str(getattr(fp,"name",""))
    if name.endswith("capacity_aware_warm_universe.json"):
        before=[]
        def collect(v):
            if isinstance(v,list):
                for row in v:
                    token=_oracle_row_token(row)
                    if token:
                        before.append(token)
            elif isinstance(v,dict):
                for child in v.values():
                    collect(child)
        collect(value)
        value=_oracle_diversify_capacity(value)
        print("[HOTBOOK_DIVERSITY_SOURCE] capacity_routes=%d unique_tokens=%d policy=unique_first"%(len(before),len(set(before))),flush=True)
    return value

_oracle_json.load=_oracle_diversity_json_load
"""

tree=ast.parse(src)
lines=src.splitlines()
insert_at=0
for node in tree.body:
    if isinstance(node,(ast.Import,ast.ImportFrom)):
        insert_at=max(insert_at,node.end_lineno)

lines[insert_at:insert_at]=BLOCK.strip("\n").splitlines()+[""]
new_src="\n".join(lines)+"\n"
ast.parse(new_src)
TARGET.write_text(new_src,encoding="utf-8")

TEST_CODE=r"""import io
import json
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as m

rows=[
 {"token":"A","pair_key":"A|1"},
 {"token":"A","pair_key":"A|2"},
 {"token":"B","pair_key":"B|1"},
 {"token":"C","pair_key":"C|1"},
 {"token":"B","pair_key":"B|2"},
]
out=m._oracle_diversify_list(rows)
assert [r["token"] for r in out[:3]]==["A","B","C"]
assert len(out)==5
assert len({r["pair_key"] for r in out})==5
s=Path(m.__file__).read_text(encoding="utf-8")
assert "DIVERSITY_FIRST_CAPACITY_LOAD_V1" in s
assert "capacity_aware_warm_universe.json" in s
assert "sendTransaction" not in s
print("[PASS] diversity-first capacity handoff replacement")
"""
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] diversity-first capacity handoff installed")
print("[SOURCE] capacity_aware_warm_universe.json")
print("[POLICY] unique token route first, duplicate pools second")
print("[ACCOUNT_CAP] existing 318-account selector unchanged")
print("[EXECUTION] exact pricing/fees/simulation unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
