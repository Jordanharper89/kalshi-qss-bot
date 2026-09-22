from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_199_CRYPTO_CONTINUOUS_VERIFIED_LEARNED_CASE_FORMATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences\nfrom .oad_188_crypto_verified_learned_case_postgresql_persistence import persist_verified_learned_cases\nfrom .oad_198_crypto_continuous_exact_outcome_maturation import mature_continuous_crypto_outcomes\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass ContinuousVerifiedLearnedCaseResult:\n    exact_outcomes:int\n    candidate_matches:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    experience_ids:tuple\n    assets:tuple\n    physical_ready:bool\n    execution_authority:bool=False\n\ndef form_continuous_verified_learned_cases(\n    root=None,\n    horizon_seconds:int=60,\n    timeout_seconds:float=120.0,\n    acquisition_timeout_seconds:float=20.0,\n    per_asset_limit:int=256,\n    now=None,\n):\n    maturity=mature_continuous_crypto_outcomes(\n        root=root,horizon_seconds=horizon_seconds,timeout_seconds=acquisition_timeout_seconds,\n        per_asset_limit=per_asset_limit,now=now\n    )\n    if not maturity.outcomes:\n        return ContinuousVerifiedLearnedCaseResult(\n            0,0,0,0,0,tuple(),tuple(),True,False\n        )\n    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)\n    by_id={x.experience_id:x for x in rb.records}\n    pairs=[]\n    for outcome in maturity.outcomes:\n        experience=by_id.get(outcome.experience_id)\n        if experience is None:\n            raise RuntimeError("exact outcome has no persisted source experience")\n        pairs.append((experience,outcome))\n    persisted=persist_verified_learned_cases(tuple(pairs),root=root,timeout_seconds=timeout_seconds)\n    ready=bool(persisted.exact_readback==len(pairs))\n    return ContinuousVerifiedLearnedCaseResult(\n        len(maturity.outcomes),len(pairs),int(persisted.already_present),int(persisted.committed_new),\n        int(persisted.exact_readback),tuple(x[0].experience_id for x in pairs),\n        tuple(sorted({x[0].asset for x in pairs})),ready,False\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_199_crypto_continuous_verified_learned_case_formation as m\n\nclass T(unittest.TestCase):\n    def test_idempotent_binding(self):\n        outcome=SimpleNamespace(experience_id="e1",asset="BTC")\n        maturity=SimpleNamespace(outcomes=(outcome,))\n        exp=SimpleNamespace(experience_id="e1",asset="BTC")\n        rb=SimpleNamespace(records=(exp,))\n        persisted=SimpleNamespace(already_present=1,committed_new=0,exact_readback=1)\n        with patch.object(m,"mature_continuous_crypto_outcomes",return_value=maturity), \\\n             patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \\\n             patch.object(m,"persist_verified_learned_cases",return_value=persisted):\n            r=m.form_continuous_verified_learned_cases()\n        print("[MATCHES]",r.candidate_matches); print("[ALREADY_PRESENT]",r.already_present); print("[READBACK]",r.exact_readback)\n        self.assertTrue(r.physical_ready)\n        self.assertEqual(r.committed_new,0)\n        self.assertEqual(r.already_present,1)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-199 continuous verified learned-case formation + idempotency certified")\n'
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
    module=pkg/'oad_199_crypto_continuous_verified_learned_case_formation.py'
    test=r/'test_oad_199_crypto_continuous_verified_learned_case_formation.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-199 CRYPTO CONTINUOUS VERIFIED LEARNED-CASE FORMATION INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_182_crypto_persisted_experience_exact_readback.py', 'oad_188_crypto_verified_learned_case_postgresql_persistence.py', 'oad_198_crypto_continuous_exact_outcome_maturation.py']:
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
        export="from .oad_199_crypto_continuous_verified_learned_case_formation import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-199 INSTALLATION COMPLETE")
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
