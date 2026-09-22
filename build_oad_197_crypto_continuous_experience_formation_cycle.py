from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_197_CRYPTO_CONTINUOUS_EXPERIENCE_FORMATION_CYCLE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_175_crypto_durable_temporal_intelligence_runtime import run_crypto_durable_temporal_intelligence\nfrom .oad_177_crypto_historical_experience_candidate import (\n    build_crypto_historical_experience_candidates,\n    verify_crypto_historical_experience_candidate,\n)\nfrom .oad_178_crypto_experience_evidence_lineage import (\n    build_crypto_experience_evidence_lineage,\n    verify_crypto_experience_evidence_lineage,\n)\nfrom .oad_179_crypto_experience_candidate_postgresql_persistence import persist_crypto_experience_candidates\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass ContinuousCryptoExperienceFormationResult:\n    snapshot_at:str\n    runtime_ready:bool\n    candidates:int\n    verified_candidates:int\n    verified_lineages:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    assets:tuple\n    experience_ids:tuple\n    physical_ready:bool\n    execution_authority:bool=False\n\ndef form_continuous_crypto_experience_cycle(\n    root=None,\n    timeout_seconds:float=120.0,\n    acquisition_timeout_seconds:float=20.0,\n    per_source_history_limit:int=512,\n    snapshot_at=None,\n):\n    runtime=run_crypto_durable_temporal_intelligence(\n        root=root,\n        timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        per_source_history_limit=per_source_history_limit,\n        snapshot_at=snapshot_at,\n    )\n    if not runtime.runtime_ready:\n        raise RuntimeError("durable temporal intelligence runtime is not ready")\n    candidates=build_crypto_historical_experience_candidates(runtime)\n    verified=tuple(x for x in candidates if verify_crypto_historical_experience_candidate(x))\n    if len(verified)!=len(candidates):\n        raise RuntimeError("continuous experience candidate verification mismatch")\n    lineages=tuple(build_crypto_experience_evidence_lineage(x) for x in verified)\n    if not all(verify_crypto_experience_evidence_lineage(x) for x in lineages):\n        raise RuntimeError("continuous experience lineage verification failed")\n    pairs=tuple(zip(verified,lineages))\n    persisted=persist_crypto_experience_candidates(pairs,root=root,timeout_seconds=timeout_seconds)\n    assets=tuple(sorted(x.asset for x in verified))\n    ids=tuple(sorted(x.experience_id for x in verified))\n    ready=bool(\n        verified and\n        persisted.exact_readback==len(verified) and\n        len(lineages)==len(verified)\n    )\n    return ContinuousCryptoExperienceFormationResult(\n        str(runtime.snapshot_at),bool(runtime.runtime_ready),len(candidates),len(verified),len(lineages),\n        int(persisted.already_present),int(persisted.committed_new),int(persisted.exact_readback),\n        assets,ids,ready,False\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_197_crypto_continuous_experience_formation_cycle as m\n\nclass T(unittest.TestCase):\n    def test_cycle_contract(self):\n        candidate=SimpleNamespace(\n            experience_id="crypto-exp:BTC:x",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00",\n            cohort_state="FULL_COVERAGE",condition_vector=(),temporal_vector=(),\n            evidence_state="CROSS_SOURCE_PRESENT",consistency_state="CONSISTENT",\n            market_native_metrics=1,independent_chain_metrics=1,comparable_temporal_metrics=0,\n            evidence_hash="a"*64,condition_hash="b"*64,experience_hash="c"*64,\n            outcome_attached=False,probability=None,direction=None,execution_authority=False\n        )\n        lineage=SimpleNamespace(asset="BTC",lineage_hash="d"*64)\n        runtime=SimpleNamespace(runtime_ready=True,snapshot_at="2026-08-30T00:00:00+00:00")\n        persistence=SimpleNamespace(already_present=0,committed_new=1,exact_readback=1)\n        with patch.object(m,"run_crypto_durable_temporal_intelligence",return_value=runtime), \\\n             patch.object(m,"build_crypto_historical_experience_candidates",return_value=(candidate,)), \\\n             patch.object(m,"verify_crypto_historical_experience_candidate",return_value=True), \\\n             patch.object(m,"build_crypto_experience_evidence_lineage",return_value=lineage), \\\n             patch.object(m,"verify_crypto_experience_evidence_lineage",return_value=True), \\\n             patch.object(m,"persist_crypto_experience_candidates",return_value=persistence):\n            r=m.form_continuous_crypto_experience_cycle()\n        print("[CANDIDATES]",r.candidates); print("[COMMITTED_NEW]",r.committed_new); print("[READY]",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertEqual(r.assets,("BTC",))\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-197 continuous crypto experience-formation cycle contract certified")\n'
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
    module=pkg/'oad_197_crypto_continuous_experience_formation_cycle.py'
    test=r/'test_oad_197_crypto_continuous_experience_formation_cycle.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-197 CRYPTO CONTINUOUS EXPERIENCE FORMATION CYCLE INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_175_crypto_durable_temporal_intelligence_runtime.py', 'oad_177_crypto_historical_experience_candidate.py', 'oad_178_crypto_experience_evidence_lineage.py', 'oad_179_crypto_experience_candidate_postgresql_persistence.py']:
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
        export="from .oad_197_crypto_continuous_experience_formation_cycle import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-197 INSTALLATION COMPLETE")
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
