from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_017_market_feedback_resolver.py"
TEST_PATH=ROOT/"test_olr_017_market_feedback_resolver.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_016_production_learned_state_adapter import ProductionLearnedStateSnapshot\n\nOLR_017_BUILD_ID="OLR-017"\nOLR_017_REVISION="OLR_017_MARKET_FEEDBACK_RESOLVER_V1"\n\n@dataclass(frozen=True)\nclass MarketFeedbackResolution:\n    market_ticker:str\n    learned_records:int\n    total_learned_records:int\n    experience_weight:float\n    eligible:bool\n    directional_signal_available:bool=False\n    execution_authority:bool=False\n\ndef resolve_market_feedback(snapshot:ProductionLearnedStateSnapshot,market_ticker:str,min_records=1):\n    counts=dict(snapshot.learned_market_counts)\n    count=int(counts.get(str(market_ticker),0))\n    weight=min(1.0,count/25.0)\n    return MarketFeedbackResolution(\n        str(market_ticker),count,snapshot.learned_records,weight,\n        count>=int(min_records),False,False\n    )\n\ndef verify_olr_017_market_feedback_resolver():\n    s=ProductionLearnedStateSnapshot("s","l",1,2,2,"h",2,2,(("KX",2),),True)\n    x=resolve_market_feedback(s,"KX")\n    return x.eligible and not x.directional_signal_available and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import ProductionLearnedStateSnapshot\nfrom qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_017_market_feedback_resolver())\n    def test_unseen_abstains(self):\n        s=ProductionLearnedStateSnapshot("s","l",0,0,0,"",0,0,tuple(),True)\n        x=resolve_market_feedback(s,"KX")\n        self.assertFalse(x.eligible);self.assertFalse(x.directional_signal_available)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-017 CERTIFICATION TEST");print(" MARKET FEEDBACK RESOLVER");print("="*72)\n    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not result.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Market-specific learned experience resolver certified")\n    print("[PASS] No directional signal fabricated from count-only learning state")\n    print("[DONE] OLR-017 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-017 INSTALLER");print(" MARKET FEEDBACK RESOLVER");print("="*72)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter')
    verifier=getattr(upstream,'verify_olr_016_production_learned_state_adapter')
    if verifier() is not True:raise RuntimeError("Upstream verification failed")
    print("[PASS] Certified upstream boundary verified")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}
    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_017_market_feedback_resolver import *"
        if line not in current:write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-017 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-017 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
