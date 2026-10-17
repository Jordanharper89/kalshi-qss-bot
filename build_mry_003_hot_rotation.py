from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_003_hot_rotation.py")
TEST=Path("test_mry_003_hot_rotation.py")

MODULE=(
    'from __future__ import annotations\nHOT_T'
    'ARGET=20\nACCOUNT_BUDGET=480\n\ndef _rank(r'
    'ow):\n    src=0 if row.get("source")=="MR'
    'IYA_HOT" else 1\n    age=row.get("source_'
    'age")\n    try:age=float(age)\n    except '
    'Exception:age=1e18\n    return (src,age,i'
    'nt(row.get("account_cost") or 999999),st'
    'r(row.get("token")))\n\ndef select_hot(inv'
    'entory,target=HOT_TARGET,account_budget='
    'ACCOUNT_BUDGET,cursor=0):\n    rows=sorte'
    'd(list(inventory or []),key=_rank)\n    i'
    'f not rows:return []\n    n=len(rows);cur'
    'sor=int(cursor)%n\n    rows=rows[cursor:]'
    '+rows[:cursor]\n    selected=[];used=0\n  '
    '  for row in rows:\n        cost=max(1,in'
    't(row.get("account_cost") or 1))\n       '
    ' if selected and used+cost>int(account_b'
    'udget):continue\n        selected.append('
    'row);used+=cost\n        if len(selected)'
    '>=int(target):break\n    return selected\n'
    '\ndef hot_view(state,selected):\n    chose'
    'n={int(x["index"]) for x in selected}\n  '
    '  preg={}\n    addresses=[]\n    old_preg='
    'state.get("preg",{})\n    for addr,item i'
    'n old_preg.items():\n        try:idx=int('
    'item[0])\n        except Exception:contin'
    'ue\n        if idx in chosen:\n           '
    ' preg[addr]=item\n            if addr not'
    ' in addresses:addresses.append(addr)\n   '
    ' view=dict(state)\n    view["preg"]=preg\n'
    '    view["addresses"]=addresses\n    view'
    '["_mry_hot_tokens"]=[str(x["token"]) for'
    ' x in selected]\n    return view\n'
)

TEST_SOURCE=(
    'import unittest\nfrom qseries_v2.oracle_e'
    'xecution.solana_atomic_executor import m'
    'ry_003_hot_rotation as m\nclass T(unittes'
    't.TestCase):\n    def test_budget(self):\n'
    '        inv=[{"index":i,"token":str(i),"'
    'account_cost":100,"source":"WARM"} for i'
    ' in range(10)]\n        s=m.select_hot(in'
    'v,target=20,account_budget=480)\n        '
    'self.assertEqual(len(s),4)\n    def test_'
    'view(self):\n        st={"pairs":[1,2],"p'
    'reg":{"a":(0,"X"),"b":(1,"Y")},"addresse'
    's":["a","b"]}\n        v=m.hot_view(st,[{'
    '"index":1,"token":"T"}])\n        self.as'
    'sertEqual(v["addresses"],["b"])\nif __nam'
    'e__=="__main__":unittest.main(verbosity='
    '2)\n'
)

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-003 installed")
print("[PASS] module: qseries_v2/oracle_execution/solana_atomic_executor/mry_003_hot_rotation.py")
print("[PASS] test: test_mry_003_hot_rotation.py")
