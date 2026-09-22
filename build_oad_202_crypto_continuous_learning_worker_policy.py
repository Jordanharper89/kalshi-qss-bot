from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_202_CRYPTO_CONTINUOUS_LEARNING_WORKER_POLICY_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoContinuousLearningWorkerPolicy:\n    cadence_seconds:float\n    horizon_seconds:int\n    acquisition_timeout_seconds:float\n    persistence_timeout_seconds:float\n    failure_backoff_base_seconds:float\n    failure_backoff_multiplier:float\n    failure_backoff_max_seconds:float\n    max_consecutive_failures_before_degraded:int\n    execution_authority:bool=False\n\ndef build_crypto_continuous_learning_worker_policy(\n    cadence_seconds:float=60.0,\n    horizon_seconds:int=60,\n    acquisition_timeout_seconds:float=20.0,\n    persistence_timeout_seconds:float=120.0,\n    failure_backoff_base_seconds:float=2.0,\n    failure_backoff_multiplier:float=2.0,\n    failure_backoff_max_seconds:float=60.0,\n    max_consecutive_failures_before_degraded:int=3,\n):\n    c=float(cadence_seconds); h=int(horizon_seconds)\n    aq=float(acquisition_timeout_seconds); ps=float(persistence_timeout_seconds)\n    b=float(failure_backoff_base_seconds); m=float(failure_backoff_multiplier); mx=float(failure_backoff_max_seconds)\n    f=int(max_consecutive_failures_before_degraded)\n    if c<=0 or h<=0 or aq<=0 or ps<=0 or b<=0 or m<1 or mx<b or f<1:\n        raise ValueError("invalid continuous-learning worker policy")\n    return CryptoContinuousLearningWorkerPolicy(c,h,aq,ps,b,m,mx,f,False)\n\ndef failure_backoff_seconds(policy,consecutive_failures:int):\n    n=max(0,int(consecutive_failures))\n    if n<=0: return 0.0\n    return min(policy.failure_backoff_max_seconds,\n               policy.failure_backoff_base_seconds*(policy.failure_backoff_multiplier**(n-1)))\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy,failure_backoff_seconds\nclass T(unittest.TestCase):\n    def test_policy(self):\n        p=build_crypto_continuous_learning_worker_policy()\n        vals=tuple(failure_backoff_seconds(p,n) for n in (1,2,3,10))\n        print("[CADENCE]",p.cadence_seconds); print("[BACKOFF]",vals)\n        self.assertEqual(vals[:3],(2.0,4.0,8.0))\n        self.assertEqual(vals[-1],60.0)\n        self.assertFalse(p.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-202 continuous-learning worker cadence/backoff policy certified")\n'
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
    module=pkg/'oad_202_crypto_continuous_learning_worker_policy.py'; test=r/'test_oad_202_crypto_continuous_learning_worker_policy.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-202 CRYPTO CONTINUOUS LEARNING WORKER POLICY INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_201_crypto_continuous_learning_24x7_physical_certification.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_202_crypto_continuous_learning_worker_policy import *"
        if export not in lines: lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-202 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
