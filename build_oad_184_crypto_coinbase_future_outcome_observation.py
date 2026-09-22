from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_184_CRYPTO_COINBASE_FUTURE_OUTCOME_OBSERVATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation,verify_outcome_observation\nfrom .oad_163_crypto_live_multi_source_cohort import acquire_target_coinbase_crypto_observations\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nPRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}\n\n@dataclass(frozen=True,slots=True)\nclass CryptoFutureOutcome:\n    experience_id:str\n    asset:str\n    horizon_seconds:int\n    start_price:float\n    outcome_price:float\n    return_fraction:float\n    return_percent:float\n    outcome_observation:object\n    source_ref:str\n    source_hash:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef experience_start_spot_price(experience):\n    rows=[x for x in tuple(experience.condition_vector) if str(x[0])=="coinbase" and str(x[1])=="spot_price"]\n    if len(rows)!=1: raise RuntimeError(f"experience {experience.experience_id} must contain exactly one Coinbase spot_price")\n    price=float(rows[0][2])\n    if price<=0: raise RuntimeError("experience start price must be positive")\n    return price\n\ndef build_crypto_future_outcome(maturity,coinbase_observation):\n    if not maturity.mature: raise ValueError("experience horizon has not expired")\n    exp=maturity.experience\n    expected=PRODUCTS.get(exp.asset)\n    if expected is None or str(coinbase_observation.subject)!=expected:\n        raise ValueError("Coinbase outcome subject mismatch")\n    start=experience_start_spot_price(exp)\n    end=float(dict(coinbase_observation.payload)["price"])\n    if end<=0: raise RuntimeError("Coinbase outcome price must be positive")\n    ret=(end/start)-1.0\n    outcome_type=f"coinbase_spot_return_{int(maturity.horizon_seconds)}s"\n    o=build_outcome_observation(\n        exp.asset,outcome_type,ret,str(coinbase_observation.observed_at),\n        str(coinbase_observation.source_id),str(coinbase_observation.provenance_hash)\n    )\n    if not verify_outcome_observation(o): raise RuntimeError("OCL-003 outcome verification failed")\n    return CryptoFutureOutcome(\n        exp.experience_id,exp.asset,int(maturity.horizon_seconds),start,end,ret,ret*100.0,\n        o,str(coinbase_observation.source_id),str(coinbase_observation.provenance_hash),True,False\n    )\n\ndef acquire_crypto_future_outcomes(maturities,timeout_seconds=20.0):\n    obs=tuple(acquire_target_coinbase_crypto_observations(timeout_seconds))\n    by_asset={str(x.subject).split("-",1)[0]:x for x in obs}\n    return tuple(build_crypto_future_outcome(m,by_asset[m.experience.asset]) for m in tuple(maturities))\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_184_crypto_coinbase_future_outcome_observation import build_crypto_future_outcome\nclass T(unittest.TestCase):\n    def test_real_contract(self):\n        exp=SimpleNamespace(experience_id="e1",asset="BTC",condition_vector=(("coinbase","spot_price",100.0,"OBSERVED"),))\n        maturity=SimpleNamespace(mature=True,experience=exp,horizon_seconds=60)\n        obs=SimpleNamespace(subject="BTC-USD",payload={"price":"105"},observed_at="2026-08-29T02:01:01Z",source_id="coinbase:BTC-USD:ticker:1",provenance_hash="a"*64)\n        x=build_crypto_future_outcome(maturity,obs)\n        print("[RETURN_PERCENT]",x.return_percent)\n        print("[OUTCOME_TYPE]",x.outcome_observation.outcome_type)\n        self.assertAlmostEqual(x.return_percent,5.0)\n        self.assertEqual(len(x.outcome_observation.outcome_hash),64)\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-184 verified Coinbase future outcome observation certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_184_crypto_coinbase_future_outcome_observation.py'; test=r/'test_oad_184_crypto_coinbase_future_outcome_observation.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-184 CRYPTO COINBASE FUTURE OUTCOME OBSERVATION INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_163_crypto_live_multi_source_cohort.py', 'oad_183_crypto_experience_outcome_maturity_gate.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in ['qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py']:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_184_crypto_coinbase_future_outcome_observation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-184 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
