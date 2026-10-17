from pathlib import Path
import ast

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_007_candidate_hydrator.py")
TEST=Path("test_mry_007_candidate_hydrator.py")

MODULE='from __future__ import annotations\nimport time\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c\nfrom . import mry_006_rpc_governor as gov\n\ndef _token_amount(raw):\n    return pd._token_amount_from_raw(raw)\n\ndef hydrate_candidate(root,row,attempts=4):\n    token=str(row["token"])\n    pump_pool=str(row["pump_pool"])\n    last=None\n\n    for attempt in range(1,int(attempts)+1):\n        try:\n            meta=row.get("meteora_meta") or c.discover_dlmm(token)\n            pump_raw,_=c.account(pump_pool)\n            pp=c.decode_pump_pool(pump_raw)\n\n            if pp["quote_mint"]!=c.WSOL:\n                raise RuntimeError("PUMP_NOT_WSOL")\n\n            base_raw,_=c.account(pp["base_vault"])\n            quote_raw,_=c.account(pp["quote_vault"])\n            lb_raw,_=c.account(meta["address"])\n            arrays=list(c.dlmm_arrays(meta["address"]))\n\n            pair=pd.PairState(\n                token=token,\n                pump_pool=pump_pool,\n                meteora_pool=meta["address"],\n                token_x=meta["token_x"],\n                token_y=meta["token_y"],\n                decimals_x=int(meta["decimals_x"]),\n                decimals_y=int(meta["decimals_y"]),\n                pump_base_vault=pp["base_vault"],\n                pump_quote_vault=pp["quote_vault"],\n                pump_base_reserve=_token_amount(base_raw),\n                pump_quote_reserve=_token_amount(quote_raw),\n                lb_bytes=lb_raw,\n                arrays=arrays,\n                dlmm_state=None,\n            )\n\n            pair.dlmm_state=pd._build_dlmm_state(pair)\n\n            print(\n                "[MRIYA_HYDRATE_READY] token=%s arrays=%d attempt=%d"\n                %(token[:10],len(arrays),attempt),\n                flush=True,\n            )\n\n            return pair\n\n        except Exception as exc:\n            last=exc\n\n            if not gov.is_rate_limited(exc) or attempt>=attempts:\n                break\n\n            delay=min(12.0,1.5*(2**(attempt-1)))\n\n            print(\n                "[MRIYA_HYDRATE_429] token=%s attempt=%d sleep=%.1f"\n                %(token[:10],attempt,delay),\n                flush=True,\n            )\n\n            time.sleep(delay)\n\n    raise RuntimeError(\n        "MRIYA_HYDRATE_FAIL:%s:%s"\n        %(type(last).__name__,last)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_execution.solana_atomic_executor import mry_007_candidate_hydrator as m\n\nclass T(unittest.TestCase):\n    def test_exports(self):\n        self.assertTrue(callable(m.hydrate_candidate))\n        self.assertTrue(callable(m._token_amount))\n\n    def test_pair_type_available(self):\n        self.assertTrue(hasattr(m.pd,"PairState"))\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-007 installed")
print("[PASS] module:",TARGET)
print("[PASS] test:",TEST)
