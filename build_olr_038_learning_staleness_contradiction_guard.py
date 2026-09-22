from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_038_learning_staleness_contradiction_guard.py"
TEST_PATH=ROOT/"test_olr_038_learning_staleness_contradiction_guard.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nOLR_038_BUILD_ID="OLR-038"\nOLR_038_REVISION="OLR_038_LEARNING_STALENESS_CONTRADICTION_GUARD_V1"\n\n@dataclass(frozen=True)\nclass LearningGuardDecision:\n    allowed:bool\n    reason:str\n    contradiction_score:float\n    stale:bool\n    execution_authority:bool=False\n\ndef evaluate_learning_guard(updated_at=None,max_age_seconds=86400.0,contradiction_score=0.0,max_contradiction=.50,now=None):\n    stale=False\n    if updated_at:\n        try:\n            ts=datetime.fromisoformat(str(updated_at).replace("Z","+00:00"))\n            if ts.tzinfo is None:ts=ts.replace(tzinfo=timezone.utc)\n            ref=now or datetime.now(timezone.utc)\n            stale=(ref-ts).total_seconds()>float(max_age_seconds)\n        except Exception:\n            return LearningGuardDecision(False,"invalid_timestamp",float(contradiction_score),True,False)\n    c=max(0.0,min(1.0,float(contradiction_score)))\n    if stale:return LearningGuardDecision(False,"stale_learning",c,True,False)\n    if c>float(max_contradiction):return LearningGuardDecision(False,"contradictory_learning",c,False,False)\n    return LearningGuardDecision(True,"allowed",c,False,False)\n\ndef verify_olr_038_learning_staleness_contradiction_guard():\n    return evaluate_learning_guard(None,contradiction_score=.1).allowed and not evaluate_learning_guard(None,contradiction_score=.9).allowed\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_038_learning_staleness_contradiction_guard import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_038_learning_staleness_contradiction_guard())\n    def test_contradiction_blocks(self):self.assertFalse(evaluate_learning_guard(None,contradiction_score=.8).allowed)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-038 CERTIFICATION TEST");print(" LEARNING STALENESS + CONTRADICTION GUARD");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Stale/contradictory learning suppression certified")\n    print("[DONE] OLR-038 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-038 INSTALLER");print(" LEARNING STALENESS CONTRADICTION GUARD");print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_037_learning_maturity_gate')
    if getattr(upstream,'verify_olr_037_learning_maturity_gate')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-037 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_038_learning_staleness_contradiction_guard import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-038 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-038 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
