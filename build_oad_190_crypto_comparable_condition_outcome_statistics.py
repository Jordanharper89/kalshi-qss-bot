from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_190_CRYPTO_COMPARABLE_CONDITION_OUTCOME_STATISTICS_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom statistics import mean,median\n\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; EXECUTION_AUTHORITY=False\n\ndef condition_signature(case):\n    cond=tuple(sorted((str(x[0]),str(x[1]),str(x[3])) for x in tuple(case.condition_vector)))\n    temp=tuple(sorted((str(x[0]),str(x[1]),str(x[2])) for x in tuple(case.temporal_vector) if len(tuple(x))>=6 and bool(tuple(x)[5])))\n    return cond,temp\n\n@dataclass(frozen=True,slots=True)\nclass ComparableConditionOutcomeStats:\n    asset:str; horizon_seconds:int; condition_signature:tuple; sample_size:int\n    positive:int; negative:int; unchanged:int; raw_positive_frequency:float\n    mean_return_percent:float; median_return_percent:float; minimum_return_percent:float; maximum_return_percent:float\n    probability_enabled:bool=False; direction_enabled:bool=False; execution_authority:bool=False\n\ndef build_comparable_condition_outcome_statistics(cases,unchanged_epsilon_percent=0.000001):\n    groups={}\n    for c in tuple(cases):\n        key=(c.asset,int(c.horizon_seconds),condition_signature(c))\n        groups.setdefault(key,[]).append(c)\n    out=[]\n    for (asset,horizon,sig),rows in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],str(x[0][2]))):\n        vals=[float(x.return_percent) for x in rows]\n        pos=sum(v>unchanged_epsilon_percent for v in vals); neg=sum(v<-unchanged_epsilon_percent for v in vals); un=len(vals)-pos-neg\n        out.append(ComparableConditionOutcomeStats(asset,horizon,sig,len(vals),pos,neg,un,pos/len(vals),mean(vals),median(vals),min(vals),max(vals),False,False,False))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics\nclass T(unittest.TestCase):\n    def test_stats(self):\n        def c(v): return SimpleNamespace(asset="BTC",horizon_seconds=60,condition_vector=(("bitcoin","fee",1,"HIGH"),),temporal_vector=(("bitcoin","fee","INCREASED",1,1,True),),return_percent=v)\n        x=build_comparable_condition_outcome_statistics((c(1),c(2),c(-1)))[0]\n        print("[SAMPLE]",x.sample_size); print("[RAW_POS_FREQ]",x.raw_positive_frequency); print("[MEAN]",x.mean_return_percent)\n        self.assertEqual(x.sample_size,3); self.assertEqual(x.positive,2); self.assertFalse(x.probability_enabled)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-190 factual comparable-condition outcome statistics certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_190_crypto_comparable_condition_outcome_statistics.py'; test=r/'test_oad_190_crypto_comparable_condition_outcome_statistics.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-190 CRYPTO COMPARABLE CONDITION OUTCOME STATISTICS INSTALLER"); print("="*118); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_189_crypto_learned_case_exact_history_readback.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_190_crypto_comparable_condition_outcome_statistics import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-190 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
