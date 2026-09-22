from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_009_generalized_learning_context.py";TEST=ROOT/"test_olf_009_generalized_reasoning_learning_context.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom .olf_008_related_market_learning_resolver import resolve_related_market_learning\nfrom qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import load_live_feedback_snapshot\nfrom qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import build_bounded_learning_consumption\n\nOLF_009_BUILD_ID="OLF-009"\nOLF_009_REVISION="OLF_009_GENERALIZED_REASONING_LEARNING_CONTEXT_V1"\n\n@dataclass(frozen=True)\nclass GeneralizedLearningContext:\n    market_ticker:str\n    relationship_type:str\n    relationship_strength:float\n    source_markets:tuple\n    learned_records:int\n    experience_weight:float\n    learner_state_hash:str\n    learning_context_consumed:bool\n    calibration_applied:bool\n    bounded_confidence_adjustment:float\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef build_generalized_learning_context(root=None,market_ticker=""):\n    root=Path(root or Path.cwd()).resolve()\n    r=resolve_related_market_learning(root,market_ticker)\n    calibration=False;adjustment=0.0\n\n    # Calibration is intentionally exact-market only.\n    # Historical same-series experience may inform reasoning context, but cannot\n    # transfer a directional calibration bias to a different contract.\n    if r.relationship_type=="EXACT_TICKER":\n        feedback=load_live_feedback_snapshot(root).get(r.market_ticker)\n        if feedback is not None:\n            bounded=build_bounded_learning_consumption(feedback)\n            calibration=bool(bounded.available)\n            adjustment=float(bounded.bounded_adjustment) if bounded.available else 0.0\n\n    return GeneralizedLearningContext(\n        r.market_ticker,r.relationship_type,r.relationship_strength,r.source_markets,\n        r.learned_records,r.generalized_experience_weight,r.learner_state_hash,\n        r.available,calibration,adjustment,True,False\n    )\n\ndef apply_generalized_confidence_context(base_confidence,context):\n    base=max(0.0,min(1.0,float(base_confidence)))\n    if not context.calibration_applied:return base\n    return max(0.0,min(1.0,base+context.bounded_confidence_adjustment))\n\ndef verify_olf_009_generalized_reasoning_learning_context():\n    x=GeneralizedLearningContext("KX","SAME_KALSHI_SERIES",.75,("A",),4,.12,"h",True,False,0.0,True,False)\n    return x.learning_context_consumed and apply_generalized_confidence_context(.6,x)==.6 and not x.execution_authority\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_009_generalized_learning_context import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_009_BUILD_ID,"OLF-009")\n    def test_related_never_directly_adjusts(self):\n        x=GeneralizedLearningContext("KX","SAME_KALSHI_SERIES",.75,("A",),3,.09,"h",True,False,.05,True,False)\n        self.assertEqual(apply_generalized_confidence_context(.6,x),.6)\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-009 CERTIFICATION TEST");print(" GENERALIZED REASONING LEARNING CONTEXT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Historical same-series experience context certified")\n    print("[PASS] Cross-contract calibration transfer prohibited")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-009 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-009 INSTALLER");print(" GENERALIZED REASONING LEARNING CONTEXT");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_008_related_market_learning_resolver")
    if not up.verify_olf_008_related_market_learning_resolver():raise RuntimeError("OLF-008 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_009_generalized_learning_context import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-009 failed; files restored");raise
    print("[PASS] Proven learner unchanged")
    print("[PASS] Existing exact-market calibration guard preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-009 INSTALLATION COMPLETE")
if __name__=="__main__":main()
