from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_021_pre_settlement_probability_recovery.py"
TEST_PATH=ROOT/"test_olr_021_pre_settlement_probability_recovery.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom typing import Any\n\nOLR_021_BUILD_ID="OLR-021"\nOLR_021_REVISION="OLR_021_PRE_SETTLEMENT_PROBABILITY_RECOVERY_V1"\n\nPROBABILITY_KEYS=(\n    "probability","yes_probability","market_probability",\n    "yes_price","last_price","price","yes_bid","yes_ask"\n)\n\n@dataclass(frozen=True)\nclass ProbabilityRecovery:\n    probability:float|None\n    source_key:str\n    raw_value:object\n    recovered:bool\n    abstain_reason:str\n\ndef _normalize_probability(value:Any):\n    try:\n        x=float(value)\n    except Exception:\n        return None\n    if 0.0 <= x <= 1.0:\n        return x\n    if 1.0 < x <= 100.0:\n        return x/100.0\n    return None\n\ndef _walk(obj,prefix=""):\n    if isinstance(obj,dict):\n        for k,v in obj.items():\n            key=f"{prefix}.{k}" if prefix else str(k)\n            yield key,k,v\n            yield from _walk(v,key)\n    elif isinstance(obj,(list,tuple)):\n        for i,v in enumerate(obj):\n            key=f"{prefix}[{i}]"\n            yield from _walk(v,key)\n\ndef recover_pre_settlement_probability(observation:dict):\n    candidates=[]\n    for path,key,value in _walk(observation):\n        lk=str(key).lower()\n        if lk in PROBABILITY_KEYS:\n            p=_normalize_probability(value)\n            if p is not None:\n                candidates.append((path,lk,p,value))\n    if not candidates:\n        return ProbabilityRecovery(None,"",None,False,"no_defensible_probability_field")\n    # Prefer explicit probability fields, then yes_price/last_price, then bid/ask.\n    rank={k:i for i,k in enumerate(PROBABILITY_KEYS)}\n    candidates.sort(key=lambda x:(rank.get(x[1],999),x[0]))\n    path,_,p,raw=candidates[0]\n    return ProbabilityRecovery(p,path,raw,True,"")\n\ndef verify_olr_021_pre_settlement_probability_recovery():\n    a=recover_pre_settlement_probability({"payload":{"yes_price":63}})\n    b=recover_pre_settlement_probability({"payload":{"foo":"bar"}})\n    return a.recovered and abs(a.probability-.63)<1e-12 and not b.recovered\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_021_pre_settlement_probability_recovery import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_021_pre_settlement_probability_recovery())\n    def test_decimal_probability(self):\n        x=recover_pre_settlement_probability({"probability":0.71})\n        self.assertAlmostEqual(x.probability,0.71)\n    def test_abstain(self):\n        self.assertFalse(recover_pre_settlement_probability({"x":1}).recovered)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-021 CERTIFICATION TEST");print(" PRE-SETTLEMENT PROBABILITY RECOVERY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Defensible probability recovery certified")\n    print("[PASS] Missing probability evidence causes abstention")\n    print("[DONE] OLR-021 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-021 INSTALLER")
    print(" PRE-SETTLEMENT PROBABILITY RECOVERY")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_020_production_feedback_runtime_gate')
    verifier=getattr(upstream,'verify_olr_020_production_feedback_runtime_gate')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-020 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_021_pre_settlement_probability_recovery import *"
        if export_line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-021 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-021 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
