from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_018_scientific_reasoning_feedback_envelope.py"
TEST_PATH=ROOT/"test_olr_018_scientific_reasoning_feedback_envelope.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_017_market_feedback_resolver import MarketFeedbackResolution\n\nOLR_018_BUILD_ID="OLR-018"\nOLR_018_REVISION="OLR_018_SCIENTIFIC_REASONING_FEEDBACK_ENVELOPE_V1"\n\n@dataclass(frozen=True)\nclass ScientificReasoningFeedbackEnvelope:\n    market_ticker:str\n    learned_records:int\n    experience_weight:float\n    feedback_eligible:bool\n    directional_adjustment:float\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef build_scientific_reasoning_feedback_envelope(resolution:MarketFeedbackResolution):\n    # Current durable OLR ledger proves experience, not directional calibration.\n    # Therefore adjustment remains exactly zero until a later certified calibration source exists.\n    return ScientificReasoningFeedbackEnvelope(\n        resolution.market_ticker,\n        resolution.learned_records,\n        resolution.experience_weight,\n        resolution.eligible,\n        0.0,\n        True,\n        False,\n    )\n\ndef verify_olr_018_scientific_reasoning_feedback_envelope():\n    r=MarketFeedbackResolution("KX",3,10,.12,True,False,False)\n    x=build_scientific_reasoning_feedback_envelope(r)\n    return x.advisory_only and x.directional_adjustment==0.0 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver import MarketFeedbackResolution\nfrom qseries_v2.oracle_learning_runtime.olr_018_scientific_reasoning_feedback_envelope import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_018_scientific_reasoning_feedback_envelope())\n    def test_no_fabricated_direction(self):\n        r=MarketFeedbackResolution("KX",100,100,1.0,True,False,False)\n        self.assertEqual(build_scientific_reasoning_feedback_envelope(r).directional_adjustment,0.0)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-018 CERTIFICATION TEST");print(" SCIENTIFIC REASONING FEEDBACK ENVELOPE");print("="*72)\n    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not result.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Advisory learned-experience envelope certified")\n    print("[PASS] Frozen reasoning remains authoritative")\n    print("[DONE] OLR-018 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-018 INSTALLER");print(" SCIENTIFIC REASONING FEEDBACK ENVELOPE");print("="*72)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver')
    verifier=getattr(upstream,'verify_olr_017_market_feedback_resolver')
    if verifier() is not True:raise RuntimeError("Upstream verification failed")
    print("[PASS] Certified upstream boundary verified")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}
    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_018_scientific_reasoning_feedback_envelope import *"
        if line not in current:write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-018 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-018 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
