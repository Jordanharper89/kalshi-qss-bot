from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_181_CRYPTO_HISTORICAL_EXPERIENCE_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_175_crypto_durable_temporal_intelligence_runtime import run_crypto_durable_temporal_intelligence\nfrom .oad_177_crypto_historical_experience_candidate import build_crypto_historical_experience_candidates,verify_crypto_historical_experience_candidate\nfrom .oad_178_crypto_experience_evidence_lineage import build_crypto_experience_evidence_lineage,verify_crypto_experience_evidence_lineage\nfrom .oad_179_crypto_experience_candidate_postgresql_persistence import persist_crypto_experience_candidates\nfrom .oad_180_crypto_experience_learning_outcome_handoff_gate import evaluate_crypto_learning_handoff\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoHistoricalExperiencePhysicalCertification:\n    runtime_ready:bool\n    candidates:int\n    verified_candidates:int\n    verified_lineages:int\n    committed_new:int\n    exact_readback:int\n    outcome_pending:int\n    learning_event_ready:int\n    assets:tuple\n    physical_ready:bool\n    certified_at:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_historical_experience_physical_certification(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0,per_source_history_limit=512):\n    runtime=run_crypto_durable_temporal_intelligence(\n        root=root,timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        per_source_history_limit=per_source_history_limit,\n    )\n    candidates=build_crypto_historical_experience_candidates(runtime)\n    lineages=tuple(build_crypto_experience_evidence_lineage(x) for x in candidates)\n    verified_candidates=sum(verify_crypto_historical_experience_candidate(x) for x in candidates)\n    verified_lineages=sum(verify_crypto_experience_evidence_lineage(x) for x in lineages)\n    pairs=tuple(zip(candidates,lineages))\n    persisted=persist_crypto_experience_candidates(pairs,root=root,timeout_seconds=timeout_seconds)\n    gates=tuple(evaluate_crypto_learning_handoff(c,l) for c,l in pairs)\n    pending=sum(x.gate_state=="HOLD_OUTCOME_REQUIRED" for x in gates)\n    ready=sum(x.learning_event_ready for x in gates)\n    assets=tuple(sorted(x.asset for x in candidates))\n    physical_ready=bool(\n        runtime.runtime_ready and candidates and verified_candidates==len(candidates)\n        and verified_lineages==len(lineages) and persisted.exact_readback==len(candidates)\n        and pending==len(candidates) and ready==0\n    )\n    if not physical_ready:\n        raise RuntimeError(\n            f"crypto experience certification failed; runtime={runtime.runtime_ready}; "\n            f"candidates={len(candidates)}; verified_candidates={verified_candidates}; "\n            f"verified_lineages={verified_lineages}; readback={persisted.exact_readback}; "\n            f"pending={pending}; learning_ready={ready}"\n        )\n    return CryptoHistoricalExperiencePhysicalCertification(\n        runtime.runtime_ready,len(candidates),verified_candidates,verified_lineages,\n        persisted.committed_new,persisted.exact_readback,pending,ready,assets,True,\n        datetime.now(timezone.utc).isoformat(),False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_181_crypto_historical_experience_physical_certification import run_crypto_historical_experience_physical_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_historical_experience_physical_certification()\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        print("[PHYSICAL] candidates=",r.candidates)\n        print("[PHYSICAL] verified_candidates=",r.verified_candidates)\n        print("[PHYSICAL] verified_lineages=",r.verified_lineages)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] outcome_pending=",r.outcome_pending)\n        print("[PHYSICAL] learning_event_ready=",r.learning_event_ready)\n        print("[PHYSICAL] assets=",r.assets)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertEqual(r.assets,("BTC","ETH","SOL"))\n        self.assertEqual(r.outcome_pending,r.candidates)\n        self.assertEqual(r.learning_event_ready,0)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-181 historical crypto experience formation physically certified")\n    print("[PASS] experience candidates persist now; OCL learning remains gated on real verified outcomes")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_181_crypto_historical_experience_physical_certification.py'; test=r/'test_oad_181_crypto_historical_experience_physical_certification.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-181 CRYPTO HISTORICAL EXPERIENCE PHYSICAL CERTIFICATION INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_175_crypto_durable_temporal_intelligence_runtime.py', 'oad_177_crypto_historical_experience_candidate.py', 'oad_178_crypto_experience_evidence_lineage.py', 'oad_179_crypto_experience_candidate_postgresql_persistence.py', 'oad_180_crypto_experience_learning_outcome_handoff_gate.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_181_crypto_historical_experience_physical_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-181 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
