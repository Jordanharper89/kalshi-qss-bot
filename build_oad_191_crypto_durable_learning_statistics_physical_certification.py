from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_191_CRYPTO_DURABLE_LEARNING_STATISTICS_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences\nfrom .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences\nfrom .oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome\nfrom .oad_188_crypto_verified_learned_case_postgresql_persistence import persist_verified_learned_cases\nfrom .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\nfrom .oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics\n\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoDurableLearningStatisticsCertification:\n    persisted_experiences:int; mature_experiences:int; exact_outcomes:int; learned_cases_written:int\n    exact_readback:int; historical_learned_cases:int; statistics_groups:int; assets:tuple; physical_ready:bool\n    certified_at:str; probability_enabled:bool=False; direction_enabled:bool=False; execution_authority:bool=False\n\ndef run_crypto_durable_learning_statistics_physical_certification(root=None,horizon_seconds=60,timeout_seconds=120.0,per_asset_limit=256):\n    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)\n    mature=select_mature_crypto_experiences(rb.records,horizon_seconds=horizon_seconds,now=datetime.now(timezone.utc),latest_per_asset=True)\n    if not mature: raise RuntimeError("no mature persisted crypto experiences")\n    outcomes=tuple(acquire_exact_coinbase_outcome(x.experience,horizon_seconds,min(20.0,float(timeout_seconds))) for x in mature)\n    pairs=tuple((m.experience,o) for m,o in zip(mature,outcomes))\n    persisted=persist_verified_learned_cases(pairs,root=root,timeout_seconds=timeout_seconds)\n    history=read_crypto_learned_case_history(root=root,per_asset_limit=512)\n    stats=build_comparable_condition_outcome_statistics(history)\n    assets=tuple(sorted({x.asset for x in history}))\n    ready=bool(outcomes and persisted.exact_readback==len(outcomes) and len(history)>=len(outcomes) and stats)\n    if not ready: raise RuntimeError(f"durable learning statistics certification failed outcomes={len(outcomes)} readback={persisted.exact_readback} history={len(history)} stats={len(stats)}")\n    return CryptoDurableLearningStatisticsCertification(rb.experiences,len(mature),len(outcomes),persisted.committed_new,persisted.exact_readback,len(history),len(stats),assets,True,datetime.now(timezone.utc).isoformat(),False,False,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_191_crypto_durable_learning_statistics_physical_certification import run_crypto_durable_learning_statistics_physical_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_durable_learning_statistics_physical_certification()\n        print("[PHYSICAL] persisted_experiences=",r.persisted_experiences)\n        print("[PHYSICAL] mature_experiences=",r.mature_experiences)\n        print("[PHYSICAL] exact_outcomes=",r.exact_outcomes)\n        print("[PHYSICAL] learned_cases_written=",r.learned_cases_written)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] historical_learned_cases=",r.historical_learned_cases)\n        print("[PHYSICAL] statistics_groups=",r.statistics_groups)\n        print("[PHYSICAL] assets=",r.assets)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready); self.assertGreater(r.exact_outcomes,0); self.assertFalse(r.probability_enabled); self.assertFalse(r.direction_enabled); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-191 durable exact-horizon crypto learning statistics physically certified")\n    print("[PASS] statistics are descriptive historical frequencies only; probability/direction/execution remain disabled")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_191_crypto_durable_learning_statistics_physical_certification.py'; test=r/'test_oad_191_crypto_durable_learning_statistics_physical_certification.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-191 CRYPTO DURABLE LEARNING STATISTICS PHYSICAL CERTIFICATION INSTALLER"); print("="*118); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_182_crypto_persisted_experience_exact_readback.py', 'oad_183_crypto_experience_outcome_maturity_gate.py', 'oad_187_crypto_exact_horizon_coinbase_outcome.py', 'oad_188_crypto_verified_learned_case_postgresql_persistence.py', 'oad_189_crypto_learned_case_exact_history_readback.py', 'oad_190_crypto_comparable_condition_outcome_statistics.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_191_crypto_durable_learning_statistics_physical_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-191 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
