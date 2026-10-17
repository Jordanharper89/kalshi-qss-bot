from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_002_warm_inventory.py")
TEST=Path("test_mry_002_warm_inventory.py")

MODULE=(
    'from __future__ import annotations\nfrom '
    'qseries_v2.oracle_strategy_intelligence.'
    'solana_money.qarb_clean_bot import live_'
    'account_stream as pd\n\nWARM_TARGET=40\n\nde'
    'f configure_hydration(target=WARM_TARGET'
    '):\n    target=max(4,int(target))\n    pd.'
    'MAX_PAIRS=max(int(getattr(pd,"MAX_PAIRS"'
    ',0)),target)\n    return target\n\ndef _pai'
    'r_cost(pair):\n    try:return len(pair.wa'
    'tched_accounts())\n    except Exception:r'
    'eturn 3+len(list(getattr(pair,"arrays",('
    ')) or ()))\n\ndef inventory(state,ready_to'
    'kens,replenishment_rows=()):\n    ready=s'
    'et(str(x) for x in (ready_tokens or ()))'
    '\n    hints={str(x.get("token")):dict(x) '
    'for x in (replenishment_rows or ()) if x'
    '.get("token")}\n    out=[]\n    for i,pair'
    ' in enumerate(list(state.get("pairs") or'
    ' [])):\n        token=str(pair.token)\n   '
    '     if token not in ready:continue\n    '
    '    h=hints.get(token,{})\n        out.ap'
    'pend({\n            "index":i,"token":tok'
    'en,"pair":pair,\n            "account_cos'
    't":_pair_cost(pair),\n            "source'
    '":str(h.get("source") or "WARM"),\n      '
    '      "source_age":h.get("age"),\n       '
    '     "pump_pool":str(pair.pump_pool),\n  '
    '          "meteora_pool":str(pair.meteor'
    'a_pool),\n        })\n    return out\n'
)

TEST_SOURCE=(
    'import unittest\nfrom types import Simple'
    'Namespace\nfrom qseries_v2.oracle_executi'
    'on.solana_atomic_executor import mry_002'
    '_warm_inventory as m\nclass T(unittest.Te'
    'stCase):\n    def test_target(self):\n    '
    '    self.assertGreaterEqual(m.configure_'
    'hydration(40),40)\n        self.assertGre'
    'aterEqual(m.pd.MAX_PAIRS,40)\n    def tes'
    't_inventory(self):\n        p=SimpleNames'
    'pace(token="A",pump_pool="P",meteora_poo'
    'l="M",arrays=[])\n        s={"pairs":[p]}'
    '\n        r=m.inventory(s,{"A"},[{"token"'
    ':"A","source":"MRIYA_HOT","age":1}])\n   '
    '     self.assertEqual(len(r),1);self.ass'
    'ertEqual(r[0]["source"],"MRIYA_HOT")\nif '
    '__name__=="__main__":unittest.main(verbo'
    'sity=2)\n'
)

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-002 installed")
print("[PASS] module: qseries_v2/oracle_execution/solana_atomic_executor/mry_002_warm_inventory.py")
print("[PASS] test: test_mry_002_warm_inventory.py")
