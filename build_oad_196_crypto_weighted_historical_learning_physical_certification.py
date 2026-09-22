from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_196_CRYPTO_WEIGHTED_HISTORICAL_LEARNING_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\nfrom .oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics\nfrom .oad_192_crypto_comparable_case_sample_sufficiency import assess_comparable_case_sufficiency\nfrom .oad_193_crypto_recency_weighted_outcome_statistics import build_recency_weighted_outcome_statistics\nfrom .oad_194_crypto_regime_relevance_weighting import build_latest_regime_profiles\nfrom .oad_195_crypto_historical_outcome_contradiction_uncertainty import build_historical_outcome_uncertainty\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass WeightedHistoricalLearningCertification:\n    historical_learned_cases:int\n    raw_statistics_groups:int\n    sufficiency_profiles:int\n    recency_profiles:int\n    regime_profiles:int\n    uncertainty_profiles:int\n    insufficient_groups:int\n    mature_descriptive_groups:int\n    assets:tuple\n    physical_ready:bool\n    certified_at:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_weighted_historical_learning_physical_certification(\n    root=None,\n    per_asset_limit:int=512,\n    half_life_seconds:int=7*24*60*60,\n):\n    history=read_crypto_learned_case_history(root=root,per_asset_limit=per_asset_limit)\n    if not history: raise RuntimeError("no verified crypto learned-case history available")\n    now=datetime.now(timezone.utc)\n    raw=build_comparable_condition_outcome_statistics(history)\n    suff=assess_comparable_case_sufficiency(raw)\n    recency=build_recency_weighted_outcome_statistics(history,reference_time=now,half_life_seconds=half_life_seconds)\n    regime=build_latest_regime_profiles(history,reference_time=now,half_life_seconds=half_life_seconds)\n    uncertainty=build_historical_outcome_uncertainty(recency)\n    assets=tuple(sorted({x.asset for x in history}))\n    ready=bool(\n        raw and len(suff)==len(raw) and len(recency)==len(raw) and regime and\n        len(uncertainty)==len(recency) and assets\n    )\n    if not ready:\n        raise RuntimeError("weighted historical-learning certification failed")\n    return WeightedHistoricalLearningCertification(\n        len(history),len(raw),len(suff),len(recency),len(regime),len(uncertainty),\n        sum(x.sufficiency_state=="INSUFFICIENT" for x in suff),\n        sum(x.sufficiency_state=="MATURE_DESCRIPTIVE" for x in suff),\n        assets,True,datetime.now(timezone.utc).isoformat(),False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_196_crypto_weighted_historical_learning_physical_certification import run_crypto_weighted_historical_learning_physical_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_weighted_historical_learning_physical_certification()\n        print("[PHYSICAL] historical_learned_cases=",r.historical_learned_cases)\n        print("[PHYSICAL] raw_statistics_groups=",r.raw_statistics_groups)\n        print("[PHYSICAL] sufficiency_profiles=",r.sufficiency_profiles)\n        print("[PHYSICAL] recency_profiles=",r.recency_profiles)\n        print("[PHYSICAL] regime_profiles=",r.regime_profiles)\n        print("[PHYSICAL] uncertainty_profiles=",r.uncertainty_profiles)\n        print("[PHYSICAL] insufficient_groups=",r.insufficient_groups)\n        print("[PHYSICAL] mature_descriptive_groups=",r.mature_descriptive_groups)\n        print("[PHYSICAL] assets=",r.assets)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertGreater(r.historical_learned_cases,0)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-196 weighted historical crypto learning physically certified")\n    print("[PASS] insufficient samples remain explicit; no probability/direction/execution enabled")\n'
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
    module=pkg/'oad_196_crypto_weighted_historical_learning_physical_certification.py'
    test=r/'test_oad_196_crypto_weighted_historical_learning_physical_certification.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-196 CRYPTO WEIGHTED HISTORICAL LEARNING PHYSICAL CERTIFICATION INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_189_crypto_learned_case_exact_history_readback.py', 'oad_190_crypto_comparable_condition_outcome_statistics.py', 'oad_192_crypto_comparable_case_sample_sufficiency.py', 'oad_193_crypto_recency_weighted_outcome_statistics.py', 'oad_194_crypto_regime_relevance_weighting.py', 'oad_195_crypto_historical_outcome_contradiction_uncertainty.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_196_crypto_weighted_historical_learning_physical_certification import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-196 INSTALLATION COMPLETE")
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
