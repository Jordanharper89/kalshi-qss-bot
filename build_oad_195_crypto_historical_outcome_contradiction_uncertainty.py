from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_195_CRYPTO_HISTORICAL_OUTCOME_CONTRADICTION_UNCERTAINTY_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom math import log\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef normalized_entropy(shares):\n    xs=[max(0.0,float(x)) for x in shares]\n    total=sum(xs)\n    if total<=0: return 1.0\n    ps=[x/total for x in xs if x>0]\n    if len(ps)<=1: return 0.0\n    h=-sum(p*log(p) for p in ps)\n    return h/log(3.0)\n\ndef contradiction_ratio(positive_share,negative_share):\n    p=max(0.0,float(positive_share)); n=max(0.0,float(negative_share))\n    d=p+n\n    return (2.0*min(p,n)/d) if d>0 else 0.0\n\n@dataclass(frozen=True,slots=True)\nclass HistoricalOutcomeUncertainty:\n    asset:str\n    horizon_seconds:int\n    raw_sample_size:int\n    effective_sample_size:float\n    positive_share:float\n    negative_share:float\n    unchanged_share:float\n    contradiction_ratio:float\n    normalized_outcome_entropy:float\n    contradiction_state:str\n    evidence_state:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef build_historical_outcome_uncertainty(recency_stats):\n    out=[]\n    for s in tuple(recency_stats):\n        cr=contradiction_ratio(s.weighted_positive_share,s.weighted_negative_share)\n        ent=normalized_entropy((s.weighted_positive_share,s.weighted_negative_share,s.weighted_unchanged_share))\n        if cr>=0.66: cs="HIGH_CONTRADICTION"\n        elif cr>=0.33: cs="MODERATE_CONTRADICTION"\n        else: cs="LOW_CONTRADICTION"\n        ess=float(s.effective_sample_size)\n        if ess<5: ev="INSUFFICIENT_EFFECTIVE_SAMPLE"\n        elif ent>=0.75: ev="HIGH_OUTCOME_UNCERTAINTY"\n        elif ent>=0.40: ev="MIXED_OUTCOME_HISTORY"\n        else: ev="CONCENTRATED_OUTCOME_HISTORY"\n        out.append(HistoricalOutcomeUncertainty(\n            s.asset,int(s.horizon_seconds),int(s.raw_sample_size),ess,\n            float(s.weighted_positive_share),float(s.weighted_negative_share),float(s.weighted_unchanged_share),\n            cr,ent,cs,ev,False,False,False\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_195_crypto_historical_outcome_contradiction_uncertainty import build_historical_outcome_uncertainty\nclass T(unittest.TestCase):\n    def test_uncertainty(self):\n        s=SimpleNamespace(asset="BTC",horizon_seconds=60,raw_sample_size=3,effective_sample_size=2.7,\n            weighted_positive_share=.5,weighted_negative_share=.5,weighted_unchanged_share=0.0)\n        x=build_historical_outcome_uncertainty((s,))[0]\n        print("[CONTRADICTION]",x.contradiction_ratio); print("[ENTROPY]",x.normalized_outcome_entropy); print("[EVIDENCE]",x.evidence_state)\n        self.assertEqual(x.contradiction_state,"HIGH_CONTRADICTION")\n        self.assertEqual(x.evidence_state,"INSUFFICIENT_EFFECTIVE_SAMPLE")\n        self.assertFalse(x.probability_enabled)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-195 historical contradiction + uncertainty intelligence certified")\n'
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
    module=pkg/'oad_195_crypto_historical_outcome_contradiction_uncertainty.py'
    test=r/'test_oad_195_crypto_historical_outcome_contradiction_uncertainty.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-195 CRYPTO HISTORICAL OUTCOME CONTRADICTION + UNCERTAINTY INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_193_crypto_recency_weighted_outcome_statistics.py', 'oad_194_crypto_regime_relevance_weighting.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_195_crypto_historical_outcome_contradiction_uncertainty import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-195 INSTALLATION COMPLETE")
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
