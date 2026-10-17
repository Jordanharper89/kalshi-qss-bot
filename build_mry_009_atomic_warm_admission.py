from pathlib import Path
import ast

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_009_atomic_warm_admission.py")
TEST=Path("test_mry_009_atomic_warm_admission.py")

MODULE='from __future__ import annotations\nimport threading\n\nLOCK=threading.RLock()\n\ndef _register_pair(state,pair):\n    token=str(pair.token)\n\n    if any(\n        str(x.token)==token\n        for x in state.get("pairs",[])\n    ):\n        return False\n\n    pairs=state.setdefault("pairs",[])\n    index=len(pairs)\n    pairs.append(pair)\n\n    preg=state.setdefault("preg",{})\n    preg[pair.pump_base_vault]=(index,"PUMP_BASE")\n    preg[pair.pump_quote_vault]=(index,"PUMP_QUOTE")\n    preg[pair.meteora_pool]=(index,"DLMM_POOL")\n\n    for j,a in enumerate(pair.arrays):\n        preg[a[1]]=(index,"DLMM_ARRAY_%d"%j)\n\n    addresses=state.setdefault("addresses",[])\n\n    for address in pair.watched_accounts():\n        if address not in addresses:\n            addresses.append(address)\n\n    eps=state.get("eps")\n\n    if eps is not None:\n        try:\n            from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as merged\n\n            eps[token].extend(\n                (\n                    merged._pump_ep(pair),\n                    merged._dlmm_ep(pair),\n                )\n            )\n\n        except Exception:\n            pass\n\n    return True\n\ndef admit(rt,state,pair,readiness):\n    token=str(pair.token)\n\n    with LOCK:\n        changed=_register_pair(\n            state,\n            pair,\n        )\n\n        rt.READY_TOKENS.add(\n            token\n        )\n\n    print(\n        "[MRIYA_WARM_ADMIT] "\n        "token=%s changed=%s warm=%d "\n        "addresses=%d forward=%s"\n        %(\n            token[:10],\n            changed,\n            len(rt.READY_TOKENS),\n            len(state.get("addresses",[])),\n            bool(readiness.get("forward")),\n        ),\n        flush=True,\n    )\n\n    return changed\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_execution.solana_atomic_executor import mry_009_atomic_warm_admission as m\n\nclass T(unittest.TestCase):\n    def test_register(self):\n        p=SimpleNamespace(\n            token="T",\n            pump_base_vault="a",\n            pump_quote_vault="b",\n            meteora_pool="c",\n            arrays=[(0,"d",b"")],\n            watched_accounts=lambda:["a","b","c","d"],\n        )\n\n        s={\n            "pairs":[],\n            "preg":{},\n            "addresses":[],\n        }\n\n        self.assertTrue(\n            m._register_pair(s,p)\n        )\n\n        self.assertFalse(\n            m._register_pair(s,p)\n        )\n\n        self.assertEqual(\n            len(s["pairs"]),\n            1,\n        )\n\n        self.assertEqual(\n            len(s["addresses"]),\n            4,\n        )\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-009 installed")
print("[PASS] module:",TARGET)
print("[PASS] test:",TEST)
