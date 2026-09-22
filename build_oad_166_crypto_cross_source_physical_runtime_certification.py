from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_166_CRYPTO_CROSS_SOURCE_PHYSICAL_RUNTIME_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_163_crypto_live_multi_source_cohort import build_crypto_live_multi_source_cohort\nfrom .oad_164_crypto_asset_chain_evidence_alignment import align_crypto_asset_chain_evidence\nfrom .oad_165_crypto_cross_source_evidence_comparison_state import build_crypto_evidence_comparison_states\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nDIRECTION_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoCrossSourcePhysicalCertification:\n    state:str\n    available_sources:tuple\n    unavailable_sources:tuple\n    total_observations:int\n    aligned_assets:int\n    ready_for_evidence_comparison_assets:int\n    ready_assets:tuple\n    runtime_ready:bool\n    certified_at:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_cross_source_physical_runtime_certification(timeout_seconds=20.0,max_coinbase_products=25,max_alignment_span_seconds=300.0):\n    cohort=build_crypto_live_multi_source_cohort(timeout_seconds,max_coinbase_products)\n    alignments=align_crypto_asset_chain_evidence(cohort)\n    states=build_crypto_evidence_comparison_states(alignments,max_alignment_span_seconds)\n    ready=tuple(x.asset for x in states if x.ready_for_evidence_comparison)\n    # Cross-source runtime is useful when Coinbase plus at least one underlying chain\n    # are simultaneously available. FULL_COVERAGE remains separately visible.\n    runtime_ready=("coinbase" in cohort.available_sources and any(x in cohort.available_sources for x in ("bitcoin","ethereum","solana")) and bool(ready))\n    if not runtime_ready:\n        raise RuntimeError("crypto cross-source runtime has no simultaneous market+chain evidence")\n    return CryptoCrossSourcePhysicalCertification(\n        cohort.state,cohort.available_sources,cohort.unavailable_sources,len(cohort.observations),\n        sum(1 for x in alignments if x.market_source_present or x.chain_source_present),\n        len(ready),ready,True,datetime.now(timezone.utc).isoformat(),True,False,False,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_166_crypto_cross_source_physical_runtime_certification import run_crypto_cross_source_physical_runtime_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_cross_source_physical_runtime_certification()\n        print("[PHYSICAL] state=",r.state)\n        print("[PHYSICAL] available_sources=",r.available_sources)\n        print("[PHYSICAL] unavailable_sources=",r.unavailable_sources)\n        print("[PHYSICAL] total_observations=",r.total_observations)\n        print("[PHYSICAL] aligned_assets=",r.aligned_assets)\n        print("[PHYSICAL] ready_for_evidence_comparison_assets=",r.ready_for_evidence_comparison_assets)\n        print("[PHYSICAL] ready_assets=",r.ready_assets)\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        self.assertTrue(r.runtime_ready); self.assertGreaterEqual(r.ready_for_evidence_comparison_assets,1)\n        self.assertFalse(r.probability_enabled); self.assertFalse(r.direction_enabled); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-166 crypto cross-source physical runtime certified")\n    print("[PASS] comparison readiness does not enable prediction, direction, or execution")\n'
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
    module=pkg/'oad_166_crypto_cross_source_physical_runtime_certification.py'; test=r/'test_oad_166_crypto_cross_source_physical_runtime_certification.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-166 CRYPTO CROSS-SOURCE PHYSICAL RUNTIME CERTIFICATION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_163_crypto_live_multi_source_cohort.py', 'oad_164_crypto_asset_chain_evidence_alignment.py', 'oad_165_crypto_cross_source_evidence_comparison_state.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_166_crypto_cross_source_physical_runtime_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-166 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
