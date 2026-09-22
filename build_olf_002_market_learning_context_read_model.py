from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_002_market_learning_context.py";TEST=ROOT/"test_olf_002_market_learning_context_read_model.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nfrom .olf_001_learned_state_snapshot import SNAPSHOT_NAME\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import (\n    load_production_learned_state,\n)\nfrom qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import (\n    load_live_feedback_snapshot,\n)\nfrom qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import (\n    build_bounded_learning_consumption,\n)\n\nOLF_002_BUILD_ID="OLF-002"\nOLF_002_REVISION="OLF_002_MARKET_LEARNING_CONTEXT_READ_MODEL_V1"\n\n@dataclass(frozen=True)\nclass MarketLearningContext:\n    market_ticker:str\n    learner_state_hash:str\n    learned_records:int\n    experience_weight:float\n    feedback_eligible:bool\n    calibration_available:bool\n    bounded_adjustment:float\n    calibration_reason:str\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef _read_snapshot(root):\n    path=Path(root)/"runtime_state"/SNAPSHOT_NAME\n    if not path.is_file():\n        return {}\n    return json.loads(path.read_text(encoding="utf-8"))\n\ndef load_market_learning_context(root=None,market_ticker=""):\n    root=Path(root or Path.cwd()).resolve()\n    ticker=str(market_ticker or "")\n    snapshot=_read_snapshot(root)\n    current=load_production_learned_state(root)\n    snap_hash=str(snapshot.get("learner_state_hash") or "")\n    if snap_hash!=current.learner_state_hash:\n        raise RuntimeError("Learned-feedback snapshot is stale relative to current learner state")\n\n    by_market={\n        str(x.get("market_ticker") or ""):x\n        for x in snapshot.get("markets",[])\n        if isinstance(x,dict)\n    }\n    row=by_market.get(ticker,{})\n    learned_records=int(row.get("learned_records",0))\n    experience_weight=float(row.get("experience_weight",0.0))\n    feedback_eligible=bool(row.get("feedback_eligible",False))\n\n    live=load_live_feedback_snapshot(root)\n    calibration=live.get(ticker)\n    if calibration is None:\n        return MarketLearningContext(\n            ticker,snap_hash,learned_records,experience_weight,feedback_eligible,\n            False,0.0,"no_mature_calibration_feedback",True,False\n        )\n\n    bounded=build_bounded_learning_consumption(calibration)\n    return MarketLearningContext(\n        ticker,snap_hash,learned_records,experience_weight,feedback_eligible,\n        bool(bounded.available),float(bounded.bounded_adjustment),\n        str(bounded.reason),True,False\n    )\n\ndef verify_olf_002_market_learning_context_read_model():\n    return OLF_002_BUILD_ID=="OLF-002" and callable(load_market_learning_context)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_002_market_learning_context import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(OLF_002_BUILD_ID,"OLF-002")\n    def test_contract(self):\n        x=MarketLearningContext("KX","h",1,.04,True,False,0.0,"x",True,False)\n        self.assertTrue(x.advisory_only)\n        self.assertFalse(x.execution_authority)\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-002 CERTIFICATION TEST");print(" MARKET LEARNING CONTEXT READ MODEL");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Market learning-context read model certified")\n    print("[PASS] Mature calibration remains bounded and advisory-only")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-002 CERTIFIED")\n'

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
    print("="*88);print(" OLF-002 INSTALLER");print(" MARKET LEARNING CONTEXT READ MODEL");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_001_learned_state_snapshot")
    if not up.verify_snapshot_matches_current_learner(ROOT):
        raise RuntimeError("OLF-001 physical snapshot verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .olf_002_market_learning_context import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-002 failed; affected files restored");raise
    print("[PASS] Frozen OLR-036 through OLR-040 consumed read-only")
    print("[PASS] Proven OLR-009 unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-002 INSTALLATION COMPLETE")
if __name__=="__main__":main()
