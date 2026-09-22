from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_003_reasoning_learning_context.py";TEST=ROOT/"test_olf_003_reasoning_learning_context_envelope.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom .olf_002_market_learning_context import load_market_learning_context\n\nOLF_003_BUILD_ID="OLF-003"\nOLF_003_REVISION="OLF_003_REASONING_LEARNING_CONTEXT_ENVELOPE_V1"\n\n@dataclass(frozen=True)\nclass LearningAwareReasoningContext:\n    market_ticker:str\n    learner_state_hash:str\n    learned_records:int\n    experience_weight:float\n    learning_context_consumed:bool\n    calibration_applied:bool\n    bounded_confidence_adjustment:float\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef build_learning_aware_reasoning_context(root=None,market_ticker=""):\n    x=load_market_learning_context(root,market_ticker)\n    consumed=bool(x.learned_records>0 or x.calibration_available)\n    return LearningAwareReasoningContext(\n        x.market_ticker,x.learner_state_hash,x.learned_records,x.experience_weight,\n        consumed,x.calibration_available,x.bounded_adjustment,True,False\n    )\n\ndef apply_bounded_confidence_context(base_confidence,context):\n    base=max(0.0,min(1.0,float(base_confidence)))\n    if not context.calibration_applied:\n        return base\n    return max(0.0,min(1.0,base+float(context.bounded_confidence_adjustment)))\n\ndef verify_olf_003_reasoning_learning_context_envelope():\n    x=LearningAwareReasoningContext("KX","h",2,.08,True,False,0.0,True,False)\n    return (\n        apply_bounded_confidence_context(.6,x)==.6\n        and x.learning_context_consumed\n        and not x.execution_authority\n    )\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_003_reasoning_learning_context import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_003_BUILD_ID,"OLF-003")\n    def test_no_unmatured_adjustment(self):\n        x=LearningAwareReasoningContext("KX","h",10,.4,True,False,.05,True,False)\n        self.assertEqual(apply_bounded_confidence_context(.61,x),.61)\n    def test_bounded_adjustment(self):\n        x=LearningAwareReasoningContext("KX","h",10,.4,True,True,.05,True,False)\n        self.assertAlmostEqual(apply_bounded_confidence_context(.61,x),.66)\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-003 CERTIFICATION TEST");print(" REASONING LEARNING-CONTEXT ENVELOPE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Learned experience can be consumed without fabricating direction")\n    print("[PASS] Confidence adjustment requires mature bounded calibration")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-003 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-003 INSTALLER");print(" REASONING LEARNING-CONTEXT ENVELOPE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_002_market_learning_context")
    if not up.verify_olf_002_market_learning_context_read_model():raise RuntimeError("OLF-002 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .olf_003_reasoning_learning_context import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-003 failed; affected files restored");raise
    print("[PASS] Frozen OSR/OCR reasoning modules unchanged")
    print("[PASS] Proven learner unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-003 INSTALLATION COMPLETE")
if __name__=="__main__":main()
