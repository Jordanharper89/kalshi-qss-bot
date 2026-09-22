from __future__ import annotations
import ast,os,textwrap
from pathlib import Path

REVISION='OAD_171_CRYPTO_CONDITION_INTELLIGENCE_PHYSICAL_RUNTIME_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_163_crypto_live_multi_source_cohort import build_crypto_live_multi_source_cohort\nfrom .oad_167_crypto_structured_condition_metric_extraction import extract_crypto_condition_metrics\nfrom .oad_168_crypto_condition_state_normalization import normalize_crypto_condition_states\nfrom .oad_169_crypto_temporal_condition_change_evaluator import evaluate_crypto_temporal_condition_changes\nfrom .oad_170_crypto_cross_source_consistency_profile import build_crypto_cross_source_consistency_profiles\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoConditionIntelligencePhysicalCertification:\n    state:str\n    available_sources:tuple\n    unavailable_sources:tuple\n    raw_observations:int\n    structured_metrics:int\n    condition_states:int\n    temporal_changes:int\n    comparable_temporal_metrics:int\n    cross_source_assets:tuple\n    profiles:tuple\n    runtime_ready:bool\n    certified_at:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_condition_intelligence_physical_runtime_certification(\n    timeout_seconds=20.0,\n    previous_states=(),\n):\n    cohort=build_crypto_live_multi_source_cohort(timeout_seconds)\n    metrics=extract_crypto_condition_metrics(cohort)\n    states=normalize_crypto_condition_states(metrics)\n    changes=evaluate_crypto_temporal_condition_changes(states,previous_states)\n    profiles=build_crypto_cross_source_consistency_profiles(states,changes)\n    cross=tuple(x.asset for x in profiles if x.evidence_state=="CROSS_SOURCE_PRESENT")\n    comparable=sum(1 for x in changes if x.comparable_history_present)\n    runtime_ready=bool(metrics and states and cross)\n    if not runtime_ready:\n        raise RuntimeError(\n            "crypto condition intelligence not ready; "\n            f"sources={tuple((x.source_family,x.state,x.observation_count,x.error_type) for x in cohort.source_states)!r}; "\n            f"metrics={len(metrics)}; cross_source_assets={cross!r}"\n        )\n    return CryptoConditionIntelligencePhysicalCertification(\n        cohort.state,cohort.available_sources,cohort.unavailable_sources,\n        len(cohort.observations),len(metrics),len(states),len(changes),comparable,\n        cross,profiles,True,datetime.now(timezone.utc).isoformat(),\n        True,False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_171_crypto_condition_intelligence_physical_runtime_certification import run_crypto_condition_intelligence_physical_runtime_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_condition_intelligence_physical_runtime_certification()\n        print("[PHYSICAL] state=",r.state)\n        print("[PHYSICAL] available_sources=",r.available_sources)\n        print("[PHYSICAL] unavailable_sources=",r.unavailable_sources)\n        print("[PHYSICAL] raw_observations=",r.raw_observations)\n        print("[PHYSICAL] structured_metrics=",r.structured_metrics)\n        print("[PHYSICAL] condition_states=",r.condition_states)\n        print("[PHYSICAL] temporal_changes=",r.temporal_changes)\n        print("[PHYSICAL] comparable_temporal_metrics=",r.comparable_temporal_metrics)\n        print("[PHYSICAL] cross_source_assets=",r.cross_source_assets)\n        print("[PHYSICAL] profiles=",tuple((x.asset,x.evidence_state,x.consistency_state,x.market_native_metrics,x.independent_chain_metrics) for x in r.profiles))\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        self.assertTrue(r.runtime_ready)\n        self.assertGreaterEqual(len(r.cross_source_assets),1)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-171 crypto condition intelligence physical runtime certified")\n    print("[PASS] condition intelligence does not enable prediction, direction, probability, or execution")\n'

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
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_171_crypto_condition_intelligence_physical_runtime_certification.py'; test=r/'test_oad_171_crypto_condition_intelligence_physical_runtime_certification.py'; init=pkg/"__init__.py"
    print("="*112)
    print(" OAD-171 CRYPTO CONDITION INTELLIGENCE PHYSICAL RUNTIME CERTIFICATION INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_163_crypto_live_multi_source_cohort.py', 'oad_167_crypto_structured_condition_metric_extraction.py', 'oad_168_crypto_condition_state_normalization.py', 'oad_169_crypto_temporal_condition_change_evaluator.py', 'oad_170_crypto_cross_source_consistency_profile.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_171_crypto_condition_intelligence_physical_runtime_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-171 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
