from __future__ import annotations
import ast,os,textwrap
from pathlib import Path

REVISION="OAD_198_FINALIZED_CANDLE_HOLD_FOUNDATIONAL_REBUILD"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences\nfrom .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences\nfrom .oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome\nfrom .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\nCOINBASE_NOT_FINALIZED_MESSAGE="no Coinbase one-minute candle at/after maturity"\n\n@dataclass(frozen=True,slots=True)\nclass ContinuousCryptoOutcomeMaturationResult:\n    pending_experiences:int\n    already_learned:int\n    mature_pending:int\n    exact_outcomes:int\n    held_not_mature:int\n    held_market_not_finalized:int\n    experience_ids:tuple\n    assets:tuple\n    outcomes:tuple\n    physical_ready:bool\n    execution_authority:bool=False\n\ndef _is_market_not_finalized(exc:Exception)->bool:\n    return isinstance(exc,RuntimeError) and COINBASE_NOT_FINALIZED_MESSAGE in str(exc)\n\ndef mature_continuous_crypto_outcomes(\n    root=None,\n    horizon_seconds:int=60,\n    timeout_seconds:float=20.0,\n    per_asset_limit:int=256,\n    now=None,\n):\n    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)\n    learned=read_crypto_learned_case_history(root=root,per_asset_limit=max(512,per_asset_limit))\n    learned_ids={x.experience_id for x in learned}\n\n    pending=tuple(x for x in rb.records if x.experience_id not in learned_ids)\n    maturities=select_mature_crypto_experiences(\n        pending,\n        horizon_seconds=horizon_seconds,\n        now=now or datetime.now(timezone.utc),\n        latest_per_asset=False,\n    )\n\n    outcomes=[]\n    held_market_not_finalized=0\n    for maturity in maturities:\n        try:\n            outcomes.append(\n                acquire_exact_coinbase_outcome(\n                    maturity.experience,\n                    horizon_seconds=horizon_seconds,\n                    timeout_seconds=timeout_seconds,\n                )\n            )\n        except Exception as exc:\n            if _is_market_not_finalized(exc):\n                held_market_not_finalized+=1\n                continue\n            raise\n\n    ids=tuple(x.experience_id for x in outcomes)\n    assets=tuple(sorted({x.asset for x in outcomes}))\n    held_not_mature=max(0,len(pending)-len(maturities))\n\n    # A maturity cycle is healthy if every mature candidate either:\n    #   (a) produced a verified exact outcome, or\n    #   (b) is waiting only for the Coinbase one-minute candle to finalize.\n    accounted=len(outcomes)+held_market_not_finalized\n    ready=bool(accounted==len(maturities))\n\n    return ContinuousCryptoOutcomeMaturationResult(\n        len(pending),\n        len(rb.records)-len(pending),\n        len(maturities),\n        len(outcomes),\n        held_not_mature,\n        held_market_not_finalized,\n        ids,\n        assets,\n        tuple(outcomes),\n        ready,\n        False,\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_198_crypto_continuous_exact_outcome_maturation as m\n\nclass T(unittest.TestCase):\n    def test_market_not_finalized_is_hold_not_failure(self):\n        p=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00")\n        rb=SimpleNamespace(records=(p,))\n        maturity=SimpleNamespace(experience=p)\n        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \\\n             patch.object(m,"read_crypto_learned_case_history",return_value=()), \\\n             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \\\n             patch.object(m,"acquire_exact_coinbase_outcome",\n                          side_effect=RuntimeError("no Coinbase one-minute candle at/after maturity")):\n            r=m.mature_continuous_crypto_outcomes()\n        print("[MATURE_PENDING]",r.mature_pending)\n        print("[EXACT_OUTCOMES]",r.exact_outcomes)\n        print("[HELD_MARKET_NOT_FINALIZED]",r.held_market_not_finalized)\n        print("[READY]",r.physical_ready)\n        self.assertEqual(r.mature_pending,1)\n        self.assertEqual(r.exact_outcomes,0)\n        self.assertEqual(r.held_market_not_finalized,1)\n        self.assertTrue(r.physical_ready)\n\n    def test_real_runtime_error_still_raises(self):\n        p=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00")\n        rb=SimpleNamespace(records=(p,))\n        maturity=SimpleNamespace(experience=p)\n        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \\\n             patch.object(m,"read_crypto_learned_case_history",return_value=()), \\\n             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \\\n             patch.object(m,"acquire_exact_coinbase_outcome",\n                          side_effect=RuntimeError("Coinbase HTTP 503")):\n            with self.assertRaisesRegex(RuntimeError,"503"):\n                m.mature_continuous_crypto_outcomes()\n\n    def test_exact_outcome_still_passes(self):\n        p=SimpleNamespace(experience_id="e2",asset="ETH",snapshot_at="2026-08-30T00:00:00+00:00")\n        rb=SimpleNamespace(records=(p,))\n        maturity=SimpleNamespace(experience=p)\n        outcome=SimpleNamespace(experience_id="e2",asset="ETH")\n        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \\\n             patch.object(m,"read_crypto_learned_case_history",return_value=()), \\\n             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \\\n             patch.object(m,"acquire_exact_coinbase_outcome",return_value=outcome):\n            r=m.mature_continuous_crypto_outcomes()\n        print("[OUTCOME_READY]",r.exact_outcomes)\n        self.assertEqual(r.exact_outcomes,1)\n        self.assertEqual(r.held_market_not_finalized,0)\n        self.assertTrue(r.physical_ready)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-198 foundational finalized-candle hold rebuild certified")\n'

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/"oad_198_crypto_continuous_exact_outcome_maturation.py"
    test=r/"test_oad_198_crypto_continuous_exact_outcome_maturation.py"
    print("="*118)
    print(" OAD-198 FINALIZED-CANDLE HOLD FOUNDATIONAL REBUILD")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)

    for dep in (
        "oad_182_crypto_persisted_experience_exact_readback.py",
        "oad_183_crypto_experience_outcome_maturity_gate.py",
        "oad_187_crypto_exact_horizon_coinbase_outcome.py",
        "oad_189_crypto_learned_case_exact_history_readback.py",
    ):
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        print("[PASS] existing OAD-198 production boundary replaced in place")
        print("[PASS] normal Coinbase candle-finalization latency now becomes HOLD, not FAILURE")
        print("[PASS] unrelated API/runtime failures still raise")
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-198 FOUNDATIONAL REBUILD COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-198 foundational rebuild rolled back")
        raise

if __name__=="__main__":
    main()
