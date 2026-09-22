from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_learning_runtime"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OLR-004'
TITLE='DURABLE CONTINUOUS LEARNING CYCLE STATE'
REVISION='OLR_004_PRODUCTION_V1'
MODULE=PACKAGE/'olr_004_learning_cycle_state.py'
TEST=ROOT/'test_olr_004_durable_continuous_learning_cycle_state.py'
EXPORTS=('OLR_004_BUILD_ID', 'OLR_004_REVISION', 'LearningRuntimeState', 'genesis_learning_runtime_state', 'load_learning_runtime_state', 'save_learning_runtime_state', 'apply_learning_inputs', 'verify_olr_004_durable_continuous_learning_cycle')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport json,os\nfrom qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import assemble_runtime_batch\nfrom qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import IncrementalLearnerState,genesis_incremental_state\nfrom qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle\nOLR_004_BUILD_ID="OLR-004"\nOLR_004_REVISION="OLR_004_DURABLE_CONTINUOUS_LEARNING_CYCLE_V1"\n\n@dataclass(frozen=True)\nclass LearningRuntimeState:\n    ocl_state:IncrementalLearnerState\n    last_settlement_ts:str\n    last_ticker:str\n    cycles:int\n    outcomes_learned:int\n\ndef genesis_learning_runtime_state():\n    return LearningRuntimeState(genesis_incremental_state(),"","",0,0)\n\ndef load_learning_runtime_state(path):\n    p=Path(path)\n    if not p.is_file():return genesis_learning_runtime_state()\n    d=json.loads(p.read_text(encoding="utf-8"))\n    return LearningRuntimeState(\n        IncrementalLearnerState(**d["ocl_state"]),\n        str(d.get("last_settlement_ts") or ""),\n        str(d.get("last_ticker") or ""),\n        int(d.get("cycles",0)),\n        int(d.get("outcomes_learned",0)),\n    )\n\ndef save_learning_runtime_state(path,state):\n    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)\n    tmp=p.with_suffix(p.suffix+".tmp")\n    tmp.write_text(json.dumps({\n        "ocl_state":asdict(state.ocl_state),\n        "last_settlement_ts":state.last_settlement_ts,\n        "last_ticker":state.last_ticker,\n        "cycles":state.cycles,\n        "outcomes_learned":state.outcomes_learned,\n    },sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,p)\n\ndef apply_learning_inputs(state,inputs,last_settlement_ts,last_ticker):\n    batch=assemble_runtime_batch(inputs)\n    result,new_ocl=run_learning_cycle(state.cycles+1,state.ocl_state,batch)\n    new=LearningRuntimeState(\n        new_ocl,last_settlement_ts,last_ticker,\n        state.cycles+1,state.outcomes_learned+len(batch.inputs)\n    )\n    return result,new\n\ndef verify_olr_004_durable_continuous_learning_cycle():\n    return genesis_learning_runtime_state().ocl_state.applied_through_sequence==0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_004_durable_continuous_learning_cycle())\nif __name__=="__main__":\n    print("="*72);print(" OLR-004 CERTIFICATION TEST");print(" DURABLE CONTINUOUS LEARNING CYCLE STATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OCL-026/027/028 cycle state binding certified")\n    print("[DONE] OLR-004 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_003_learning_event_bridge')
        if getattr(m,'verify_olr_003_evidence_outcome_learning_event_bridge')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified frozen upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_learning_runtime."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
