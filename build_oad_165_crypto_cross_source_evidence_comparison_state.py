from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_165_CRYPTO_CROSS_SOURCE_EVIDENCE_COMPARISON_STATE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nDIRECTION_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoEvidenceComparisonState:\n    asset:str\n    state:str\n    market_observation_count:int\n    chain_observation_count:int\n    observation_time_span_seconds:float|None\n    independent_chain_evidence:bool\n    market_native_reference:bool\n    ready_for_evidence_comparison:bool\n    ready_for_prediction:bool=False\n    direction:None=None\n    probability:None=None\n\ndef build_crypto_evidence_comparison_states(alignments,max_alignment_span_seconds=300.0):\n    out=[]\n    for a in tuple(alignments):\n        span=a.observation_time_span_seconds\n        fresh=(span is None or span<=float(max_alignment_span_seconds))\n        ready=bool(a.evidence_comparison_possible and fresh)\n        if ready: state="READY_FOR_EVIDENCE_COMPARISON"\n        elif a.market_source_present or a.chain_source_present: state="OBSERVE"\n        else: state="NO_CURRENT_EVIDENCE"\n        out.append(CryptoEvidenceComparisonState(\n            a.asset,state,len(a.market_observations),len(a.chain_observations),span,\n            bool(a.chain_source_present),bool(a.market_source_present),ready,False,None,None))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_165_crypto_cross_source_evidence_comparison_state import build_crypto_evidence_comparison_states\nclass T(unittest.TestCase):\n    def test_state(self):\n        a=SimpleNamespace(asset="BTC",market_observations=(1,),chain_observations=(2,3),observation_time_span_seconds=10.0,evidence_comparison_possible=True,market_source_present=True,chain_source_present=True)\n        r=build_crypto_evidence_comparison_states((a,))[0]\n        print("[STATE]",r.state); print("[READY_COMPARISON]",r.ready_for_evidence_comparison); print("[READY_PREDICTION]",r.ready_for_prediction)\n        self.assertTrue(r.ready_for_evidence_comparison); self.assertFalse(r.ready_for_prediction); self.assertIsNone(r.direction); self.assertIsNone(r.probability)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-165 cross-source evidence comparison state certified")\n'
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
    module=pkg/'oad_165_crypto_cross_source_evidence_comparison_state.py'; test=r/'test_oad_165_crypto_cross_source_evidence_comparison_state.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-165 CRYPTO CROSS-SOURCE EVIDENCE COMPARISON STATE INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_164_crypto_asset_chain_evidence_alignment.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_165_crypto_cross_source_evidence_comparison_state import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-165 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
