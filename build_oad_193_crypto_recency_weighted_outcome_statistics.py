from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_193_CRYPTO_RECENCY_WEIGHTED_OUTCOME_STATISTICS_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom math import exp,log\nfrom .oad_190_crypto_comparable_condition_outcome_statistics import condition_signature\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nDEFAULT_HALF_LIFE_SECONDS=7*24*60*60\n\ndef _dt(v):\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n\ndef _weight(age_seconds,half_life_seconds):\n    return exp(-log(2.0)*max(0.0,float(age_seconds))/float(half_life_seconds))\n\n@dataclass(frozen=True,slots=True)\nclass RecencyWeightedOutcomeStats:\n    asset:str\n    horizon_seconds:int\n    condition_signature:tuple\n    raw_sample_size:int\n    total_weight:float\n    effective_sample_size:float\n    weighted_positive_share:float\n    weighted_negative_share:float\n    weighted_unchanged_share:float\n    weighted_mean_return_percent:float\n    half_life_seconds:int\n    reference_time:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef build_recency_weighted_outcome_statistics(\n    cases,\n    reference_time=None,\n    half_life_seconds:int=DEFAULT_HALF_LIFE_SECONDS,\n    unchanged_epsilon_percent:float=0.000001,\n):\n    if int(half_life_seconds)<=0: raise ValueError("half_life_seconds must be > 0")\n    ref=_dt(reference_time or datetime.now(timezone.utc))\n    groups={}\n    for c in tuple(cases):\n        groups.setdefault((c.asset,int(c.horizon_seconds),condition_signature(c)),[]).append(c)\n    out=[]\n    for (asset,horizon,sig),rows in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],str(x[0][2]))):\n        weighted=[]\n        for c in rows:\n            age=(ref-_dt(c.outcome_observed_at)).total_seconds()\n            w=_weight(age,half_life_seconds)\n            weighted.append((c,w))\n        sw=sum(w for _,w in weighted)\n        sw2=sum(w*w for _,w in weighted)\n        if sw<=0: raise RuntimeError("recency weighting produced zero total weight")\n        pos=sum(w for c,w in weighted if float(c.return_percent)>unchanged_epsilon_percent)\n        neg=sum(w for c,w in weighted if float(c.return_percent)<-unchanged_epsilon_percent)\n        un=sw-pos-neg\n        mean_ret=sum(float(c.return_percent)*w for c,w in weighted)/sw\n        ess=(sw*sw/sw2) if sw2>0 else 0.0\n        out.append(RecencyWeightedOutcomeStats(\n            asset,horizon,sig,len(rows),sw,ess,pos/sw,neg/sw,un/sw,mean_ret,\n            int(half_life_seconds),ref.isoformat(),False,False,False\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_193_crypto_recency_weighted_outcome_statistics import build_recency_weighted_outcome_statistics\nclass T(unittest.TestCase):\n    def test_recency(self):\n        def c(ts,v):\n            return SimpleNamespace(asset="BTC",horizon_seconds=60,\n                condition_vector=(("bitcoin","fee",1,"HIGH"),),\n                temporal_vector=(("bitcoin","fee","INCREASED",1,1,True),),\n                outcome_observed_at=ts,return_percent=v)\n        rows=build_recency_weighted_outcome_statistics(\n            (c("2026-08-29T00:00:00+00:00",-1.0),c("2026-08-30T00:00:00+00:00",2.0)),\n            reference_time="2026-08-30T00:00:00+00:00",half_life_seconds=86400\n        )\n        x=rows[0]\n        print("[RAW_N]",x.raw_sample_size); print("[ESS]",x.effective_sample_size); print("[WEIGHTED_POS_SHARE]",x.weighted_positive_share)\n        self.assertEqual(x.raw_sample_size,2)\n        self.assertGreater(x.weighted_positive_share,0.5)\n        self.assertFalse(x.probability_enabled)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-193 recency-weighted descriptive outcome statistics certified")\n'
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
    module=pkg/'oad_193_crypto_recency_weighted_outcome_statistics.py'
    test=r/'test_oad_193_crypto_recency_weighted_outcome_statistics.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-193 CRYPTO RECENCY-WEIGHTED OUTCOME STATISTICS INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_189_crypto_learned_case_exact_history_readback.py', 'oad_190_crypto_comparable_condition_outcome_statistics.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_193_crypto_recency_weighted_outcome_statistics import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-193 INSTALLATION COMPLETE")
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
