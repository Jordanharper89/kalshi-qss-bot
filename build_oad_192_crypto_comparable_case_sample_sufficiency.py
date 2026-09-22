from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_192_CRYPTO_COMPARABLE_CASE_SAMPLE_SUFFICIENCY_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\nDEFAULT_PRELIMINARY_MIN=5\nDEFAULT_DEVELOPING_MIN=20\nDEFAULT_MATURE_MIN=100\n\n@dataclass(frozen=True,slots=True)\nclass ComparableCaseSufficiency:\n    asset:str\n    horizon_seconds:int\n    condition_signature:tuple\n    sample_size:int\n    sufficiency_state:str\n    threshold_to_next_state:int\n    cases_needed_to_next_state:int\n    descriptive_statistics_usable:bool\n    predictive_probability_eligible:bool=False\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef classify_sample_sufficiency(\n    sample_size:int,\n    preliminary_min:int=DEFAULT_PRELIMINARY_MIN,\n    developing_min:int=DEFAULT_DEVELOPING_MIN,\n    mature_min:int=DEFAULT_MATURE_MIN,\n):\n    n=int(sample_size)\n    if n<0: raise ValueError("sample_size must be >= 0")\n    a,b,c=int(preliminary_min),int(developing_min),int(mature_min)\n    if not (1 <= a < b < c):\n        raise ValueError("sufficiency thresholds must satisfy 1 <= preliminary < developing < mature")\n    if n<a:\n        return "INSUFFICIENT",a,a-n\n    if n<b:\n        return "PRELIMINARY",b,b-n\n    if n<c:\n        return "DEVELOPING",c,c-n\n    return "MATURE_DESCRIPTIVE",c,0\n\ndef assess_comparable_case_sufficiency(\n    stats,\n    preliminary_min:int=DEFAULT_PRELIMINARY_MIN,\n    developing_min:int=DEFAULT_DEVELOPING_MIN,\n    mature_min:int=DEFAULT_MATURE_MIN,\n):\n    out=[]\n    for s in tuple(stats):\n        state,next_threshold,needed=classify_sample_sufficiency(\n            s.sample_size,preliminary_min,developing_min,mature_min\n        )\n        out.append(ComparableCaseSufficiency(\n            s.asset,int(s.horizon_seconds),tuple(s.condition_signature),int(s.sample_size),\n            state,next_threshold,needed,bool(s.sample_size>0),\n            False,False,False,False\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_192_crypto_comparable_case_sample_sufficiency import assess_comparable_case_sufficiency\nclass T(unittest.TestCase):\n    def test_states(self):\n        stats=(\n            SimpleNamespace(asset="BTC",horizon_seconds=60,condition_signature=(("x",),),sample_size=3),\n            SimpleNamespace(asset="ETH",horizon_seconds=60,condition_signature=(("y",),),sample_size=25),\n            SimpleNamespace(asset="SOL",horizon_seconds=60,condition_signature=(("z",),),sample_size=120),\n        )\n        rows=assess_comparable_case_sufficiency(stats)\n        print("[STATES]",tuple(x.sufficiency_state for x in rows))\n        print("[NEEDED]",tuple(x.cases_needed_to_next_state for x in rows))\n        self.assertEqual(rows[0].sufficiency_state,"INSUFFICIENT")\n        self.assertEqual(rows[1].sufficiency_state,"DEVELOPING")\n        self.assertEqual(rows[2].sufficiency_state,"MATURE_DESCRIPTIVE")\n        self.assertFalse(any(x.predictive_probability_eligible for x in rows))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-192 explicit comparable-case sample sufficiency certified")\n'
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
    module=pkg/'oad_192_crypto_comparable_case_sample_sufficiency.py'
    test=r/'test_oad_192_crypto_comparable_case_sample_sufficiency.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-192 CRYPTO COMPARABLE-CASE SAMPLE SUFFICIENCY INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_190_crypto_comparable_condition_outcome_statistics.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_192_crypto_comparable_case_sample_sufficiency import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-192 INSTALLATION COMPLETE")
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
