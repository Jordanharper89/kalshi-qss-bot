from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_198_CRYPTO_CONTINUOUS_EXACT_OUTCOME_MATURATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences\nfrom .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences\nfrom .oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome\nfrom .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass ContinuousCryptoOutcomeMaturationResult:\n    pending_experiences:int\n    already_learned:int\n    mature_pending:int\n    exact_outcomes:int\n    held_not_mature:int\n    experience_ids:tuple\n    assets:tuple\n    outcomes:tuple\n    physical_ready:bool\n    execution_authority:bool=False\n\ndef mature_continuous_crypto_outcomes(\n    root=None,\n    horizon_seconds:int=60,\n    timeout_seconds:float=20.0,\n    per_asset_limit:int=256,\n    now=None,\n):\n    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)\n    learned=read_crypto_learned_case_history(root=root,per_asset_limit=max(512,per_asset_limit))\n    learned_ids={x.experience_id for x in learned}\n    pending=tuple(x for x in rb.records if x.experience_id not in learned_ids)\n    maturities=select_mature_crypto_experiences(\n        pending,horizon_seconds=horizon_seconds,now=now or datetime.now(timezone.utc),latest_per_asset=False\n    )\n    outcomes=[]\n    for maturity in maturities:\n        outcomes.append(acquire_exact_coinbase_outcome(\n            maturity.experience,horizon_seconds=horizon_seconds,timeout_seconds=timeout_seconds\n        ))\n    ids=tuple(x.experience_id for x in outcomes)\n    assets=tuple(sorted({x.asset for x in outcomes}))\n    held=max(0,len(pending)-len(maturities))\n    ready=bool(len(outcomes)==len(maturities))\n    return ContinuousCryptoOutcomeMaturationResult(\n        len(pending),len(rb.records)-len(pending),len(maturities),len(outcomes),held,\n        ids,assets,tuple(outcomes),ready,False\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_198_crypto_continuous_exact_outcome_maturation as m\n\nclass T(unittest.TestCase):\n    def test_excludes_already_learned(self):\n        p1=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00")\n        p2=SimpleNamespace(experience_id="e2",asset="ETH",snapshot_at="2026-08-30T00:00:00+00:00")\n        rb=SimpleNamespace(records=(p1,p2))\n        learned=(SimpleNamespace(experience_id="e1"),)\n        maturity=SimpleNamespace(experience=p2)\n        outcome=SimpleNamespace(experience_id="e2",asset="ETH")\n        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \\\n             patch.object(m,"read_crypto_learned_case_history",return_value=learned), \\\n             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \\\n             patch.object(m,"acquire_exact_coinbase_outcome",return_value=outcome):\n            r=m.mature_continuous_crypto_outcomes()\n        print("[PENDING]",r.pending_experiences); print("[ALREADY_LEARNED]",r.already_learned); print("[OUTCOMES]",r.exact_outcomes)\n        self.assertEqual(r.pending_experiences,1)\n        self.assertEqual(r.already_learned,1)\n        self.assertEqual(r.experience_ids,("e2",))\n        self.assertTrue(r.physical_ready)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-198 continuous exact-outcome maturation + learned-case exclusion certified")\n'
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
    module=pkg/'oad_198_crypto_continuous_exact_outcome_maturation.py'
    test=r/'test_oad_198_crypto_continuous_exact_outcome_maturation.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-198 CRYPTO CONTINUOUS EXACT-OUTCOME MATURATION INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_182_crypto_persisted_experience_exact_readback.py', 'oad_183_crypto_experience_outcome_maturity_gate.py', 'oad_187_crypto_exact_horizon_coinbase_outcome.py', 'oad_189_crypto_learned_case_exact_history_readback.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file():
            raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_198_crypto_continuous_exact_outcome_maturation import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-198 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__":
    main()
