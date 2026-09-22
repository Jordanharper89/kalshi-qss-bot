from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_194_CRYPTO_REGIME_RELEVANCE_WEIGHTING_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom math import exp,log\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nDEFAULT_HALF_LIFE_SECONDS=7*24*60*60\n\ndef _dt(v):\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n\ndef regime_tokens(case):\n    tokens=set()\n    for x in tuple(case.condition_vector):\n        if len(tuple(x))>=4:\n            tokens.add(("condition",str(x[0]),str(x[1]),str(x[3])))\n    for x in tuple(case.temporal_vector):\n        if len(tuple(x))>=6 and bool(tuple(x)[5]):\n            tokens.add(("temporal",str(x[0]),str(x[1]),str(x[2])))\n    return frozenset(tokens)\n\ndef jaccard_similarity(a,b):\n    a,b=set(a),set(b)\n    if not a and not b: return 1.0\n    if not a or not b: return 0.0\n    return len(a & b)/len(a | b)\n\n@dataclass(frozen=True,slots=True)\nclass RegimeWeightedOutcomeProfile:\n    asset:str\n    horizon_seconds:int\n    reference_experience_id:str\n    historical_case_count:int\n    nonzero_relevance_cases:int\n    total_combined_weight:float\n    effective_sample_size:float\n    weighted_positive_share:float\n    weighted_negative_share:float\n    weighted_unchanged_share:float\n    weighted_mean_return_percent:float\n    mean_regime_similarity:float\n    half_life_seconds:int\n    reference_time:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef build_regime_relevance_weighted_profile(\n    reference_case,\n    historical_cases,\n    reference_time=None,\n    half_life_seconds:int=DEFAULT_HALF_LIFE_SECONDS,\n    unchanged_epsilon_percent:float=0.000001,\n):\n    if int(half_life_seconds)<=0: raise ValueError("half_life_seconds must be > 0")\n    ref_time=_dt(reference_time or datetime.now(timezone.utc))\n    ref_tokens=regime_tokens(reference_case)\n    pool=[c for c in tuple(historical_cases)\n          if c.asset==reference_case.asset and int(c.horizon_seconds)==int(reference_case.horizon_seconds)]\n    weighted=[]\n    sims=[]\n    for c in pool:\n        sim=jaccard_similarity(ref_tokens,regime_tokens(c))\n        age=max(0.0,(ref_time-_dt(c.outcome_observed_at)).total_seconds())\n        recency=exp(-log(2.0)*age/float(half_life_seconds))\n        w=sim*recency\n        sims.append(sim)\n        weighted.append((c,w))\n    sw=sum(w for _,w in weighted); sw2=sum(w*w for _,w in weighted)\n    pos=sum(w for c,w in weighted if float(c.return_percent)>unchanged_epsilon_percent)\n    neg=sum(w for c,w in weighted if float(c.return_percent)<-unchanged_epsilon_percent)\n    un=sw-pos-neg\n    mean_ret=sum(float(c.return_percent)*w for c,w in weighted)/sw if sw>0 else 0.0\n    ess=(sw*sw/sw2) if sw2>0 else 0.0\n    return RegimeWeightedOutcomeProfile(\n        reference_case.asset,int(reference_case.horizon_seconds),reference_case.experience_id,\n        len(pool),sum(1 for _,w in weighted if w>0),sw,ess,\n        pos/sw if sw>0 else 0.0,neg/sw if sw>0 else 0.0,un/sw if sw>0 else 0.0,\n        mean_ret,sum(sims)/len(sims) if sims else 0.0,int(half_life_seconds),ref_time.isoformat(),\n        False,False,False\n    )\n\ndef build_latest_regime_profiles(cases,reference_time=None,half_life_seconds:int=DEFAULT_HALF_LIFE_SECONDS):\n    rows=tuple(cases)\n    latest={}\n    for c in rows:\n        key=(c.asset,int(c.horizon_seconds))\n        if key not in latest or str(c.outcome_observed_at)>str(latest[key].outcome_observed_at):\n            latest[key]=c\n    return tuple(build_regime_relevance_weighted_profile(\n        latest[k],rows,reference_time,half_life_seconds\n    ) for k in sorted(latest))\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_194_crypto_regime_relevance_weighting import build_regime_relevance_weighted_profile\nclass T(unittest.TestCase):\n    def test_regime(self):\n        def c(e,state,trend,ts,v):\n            return SimpleNamespace(asset="BTC",horizon_seconds=60,experience_id=e,\n                condition_vector=(("bitcoin","fee",1,state),),\n                temporal_vector=(("bitcoin","fee",trend,1,1,True),),\n                outcome_observed_at=ts,return_percent=v)\n        ref=c("new","HIGH","INCREASED","2026-08-30T00:00:00+00:00",2)\n        old_same=c("same","HIGH","INCREASED","2026-08-29T00:00:00+00:00",1)\n        old_diff=c("diff","LOW","DECREASED","2026-08-29T00:00:00+00:00",-1)\n        x=build_regime_relevance_weighted_profile(ref,(old_same,old_diff),reference_time="2026-08-30T00:00:00+00:00",half_life_seconds=86400)\n        print("[CASES]",x.historical_case_count); print("[MEAN_SIM]",x.mean_regime_similarity); print("[ESS]",x.effective_sample_size)\n        self.assertEqual(x.historical_case_count,2)\n        self.assertGreater(x.weighted_positive_share,x.weighted_negative_share)\n        self.assertFalse(x.probability_enabled)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-194 regime-similarity + recency relevance weighting certified")\n'
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
    module=pkg/'oad_194_crypto_regime_relevance_weighting.py'
    test=r/'test_oad_194_crypto_regime_relevance_weighting.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-194 CRYPTO REGIME-RELEVANCE WEIGHTING INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_189_crypto_learned_case_exact_history_readback.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_194_crypto_regime_relevance_weighting import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-194 INSTALLATION COMPLETE")
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
