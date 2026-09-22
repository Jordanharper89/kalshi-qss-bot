from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_016_production_learned_state_adapter.py"
TEST_PATH=ROOT/"test_olr_016_production_learned_state_adapter.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nOLR_016_BUILD_ID="OLR-016"\nOLR_016_REVISION="OLR_016_PRODUCTION_LEARNED_STATE_ADAPTER_V1"\n\n@dataclass(frozen=True)\nclass ProductionLearnedStateSnapshot:\n    source_state_path:str\n    source_ledger_path:str\n    cycles:int\n    outcomes_learned:int\n    applied_through_sequence:int\n    learner_state_hash:str\n    ledger_records:int\n    learned_records:int\n    learned_market_counts:tuple\n    read_only:bool=True\n\ndef _read_json(path):\n    p=Path(path)\n    if not p.is_file():\n        return {}\n    return json.loads(p.read_text(encoding="utf-8"))\n\ndef load_production_learned_state(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    state_path=root/"runtime_state"/"oracle_learning_runtime_state.json"\n    ledger_path=root/"runtime_state"/"oracle_learning_event_ledger.json"\n    state=_read_json(state_path)\n    ledger=_read_json(ledger_path)\n\n    ocl=state.get("ocl_state") if isinstance(state,dict) else {}\n    if not isinstance(ocl,dict):ocl={}\n    counts={}\n    learned=0\n    if isinstance(ledger,dict):\n        for rec in ledger.values():\n            if not isinstance(rec,dict):continue\n            if str(rec.get("status") or "")!="learned":continue\n            learned+=1\n            ticker=str(rec.get("ticker") or "")\n            if ticker:counts[ticker]=counts.get(ticker,0)+1\n\n    return ProductionLearnedStateSnapshot(\n        str(state_path.relative_to(root)),\n        str(ledger_path.relative_to(root)),\n        int(state.get("cycles",0)) if isinstance(state,dict) else 0,\n        int(state.get("outcomes_learned",0)) if isinstance(state,dict) else 0,\n        int(ocl.get("applied_through_sequence",0)),\n        str(ocl.get("state_hash") or ""),\n        len(ledger) if isinstance(ledger,dict) else 0,\n        learned,\n        tuple(sorted(counts.items())),\n        True,\n    )\n\ndef verify_olr_016_production_learned_state_adapter():\n    x=load_production_learned_state(Path("__olr_missing_root__"))\n    return x.read_only and x.cycles==0 and x.ledger_records==0\n'
TEST_SOURCE='import tempfile,unittest,json\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_016_production_learned_state_adapter())\n    def test_real_shape(self):\n        with tempfile.TemporaryDirectory() as d:\n            r=Path(d);(r/"runtime_state").mkdir()\n            (r/"runtime_state"/"oracle_learning_runtime_state.json").write_text(json.dumps({"cycles":2,"outcomes_learned":3,"ocl_state":{"applied_through_sequence":3,"state_hash":"abc"}}))\n            (r/"runtime_state"/"oracle_learning_event_ledger.json").write_text(json.dumps({"a":{"status":"learned","ticker":"KX"},"b":{"status":"learned","ticker":"KX"}}))\n            x=load_production_learned_state(r)\n            self.assertEqual(x.learned_market_counts,(("KX",2),))\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-016 CERTIFICATION TEST");print(" PRODUCTION LEARNED-STATE ADAPTER");print("="*72)\n    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not result.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Durable OLR state + ledger read adapter certified")\n    print("[DONE] OLR-016 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-016 INSTALLER");print(" PRODUCTION LEARNED-STATE ADAPTER");print("="*72)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_015_learned_state_feedback_runtime_gate')
    verifier=getattr(upstream,'verify_olr_015_learned_state_feedback_runtime_gate')
    if verifier() is not True:raise RuntimeError("Upstream verification failed")
    print("[PASS] Certified upstream boundary verified")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}
    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_016_production_learned_state_adapter import *"
        if line not in current:write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-016 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-016 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
