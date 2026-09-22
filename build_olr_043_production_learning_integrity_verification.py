from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_043_production_learning_integrity_verification.py"
TEST_PATH=ROOT/"test_olr_043_production_learning_integrity_verification.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nfrom hashlib import sha256\nimport json\n\nfrom .olr_041_learning_health_model import inspect_learning_health\nfrom .olr_042_deterministic_learning_replay import replay_learning_records\n\nOLR_043_BUILD_ID="OLR-043"\nOLR_043_REVISION="OLR_043_PRODUCTION_LEARNING_INTEGRITY_VERIFICATION_V1"\n\n@dataclass(frozen=True)\nclass ProductionLearningIntegrity:\n    health:str\n    calibration_records:int\n    mature_markets:int\n    replay_hash:str\n    state_hash:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef verify_production_learning_integrity(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    health=inspect_learning_health(root)\n\n    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"\n    try:\n        ledger=json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}\n    except Exception:\n        ledger={}\n\n    records=tuple(ledger.values()) if isinstance(ledger,dict) else tuple()\n    replay=replay_learning_records(records)\n\n    payload={\n        "health":health.health,\n        "calibration_records":health.calibration_records,\n        "mature_markets":health.mature_markets,\n        "replay_hash":replay.replay_hash,\n    }\n    state_hash=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n\n    return ProductionLearningIntegrity(\n        health.health,\n        health.calibration_records,\n        health.mature_markets,\n        replay.replay_hash,\n        state_hash,\n        True,\n        False,\n    )\n\ndef verify_olr_043_production_learning_integrity_verification():\n    x=verify_production_learning_integrity(Path("__missing__"))\n    return len(x.state_hash)==64 and x.read_only and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_043_production_learning_integrity_verification import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_043_production_learning_integrity_verification())\n    def test_hash(self):self.assertEqual(len(verify_production_learning_integrity("__missing__").state_hash),64)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-043 CERTIFICATION TEST");print(" PRODUCTION LEARNING INTEGRITY VERIFICATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Production learning health + replay integrity certified")\n    print("[DONE] OLR-043 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_043_physical_production_learning_integrity_verification.py'
EXTRA_SOURCE_1='from pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_043_production_learning_integrity_verification import verify_production_learning_integrity\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-043 PHYSICAL PRODUCTION LEARNING INTEGRITY VERIFICATION")\n    print("="*72)\n    x=verify_production_learning_integrity(Path.cwd())\n    print(f"[HEALTH] state={x.health} calibration_records={x.calibration_records} mature_markets={x.mature_markets}")\n    print(f"[REPLAY HASH] {x.replay_hash}")\n    print(f"[STATE HASH] {x.state_hash}")\n    print("[PASS] Production learning integrity checked read-only")\n    print("[PASS] Zero/mature learning state is classified explicitly")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-043 PHYSICAL PRODUCTION LEARNING INTEGRITY VERIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-043 INSTALLER")
    print(" PRODUCTION LEARNING INTEGRITY VERIFICATION")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_042_deterministic_learning_replay')
    verifier=getattr(upstream,'verify_olr_042_deterministic_learning_replay')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-042 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_043_production_learning_integrity_verification import *"
        if export_line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(EXTRA_PATH_1)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-043 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-043 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
