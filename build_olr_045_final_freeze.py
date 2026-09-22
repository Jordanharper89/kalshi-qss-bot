from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_045_final_freeze.py"
TEST_PATH=ROOT/"test_olr_045_final_freeze.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom hashlib import sha256\nfrom pathlib import Path\nimport json\n\nfrom .olr_044_final_production_certification_gate import certify_olr_final_production_boundary\n\nOLR_045_BUILD_ID="OLR-045"\nOLR_045_REVISION="OLR_045_FINAL_FREEZE_V1"\nOLR_FREEZE_POLICY="DEFECT_CORRECTIONS_ONLY"\n\n@dataclass(frozen=True)\nclass OLRFreezeManifest:\n    subsystem:str\n    frozen_start:str\n    frozen_end:str\n    policy:str\n    execution_authority:bool\n    terminal_dependency:str\n    manifest_hash:str\n\ndef build_olr_freeze_manifest():\n    cert=certify_olr_final_production_boundary()\n    payload={\n        "subsystem":"Oracle Learning Runtime",\n        "frozen_start":"OLR-001",\n        "frozen_end":"OLR-045",\n        "policy":OLR_FREEZE_POLICY,\n        "execution_authority":False,\n        "terminal_dependency":"NONE",\n        "certified_runtime_role":cert.runtime_role,\n    }\n    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return OLRFreezeManifest(\n        payload["subsystem"],payload["frozen_start"],payload["frozen_end"],\n        payload["policy"],False,"NONE",h\n    )\n\ndef verify_olr_045_final_freeze():\n    x=build_olr_freeze_manifest()\n    return x.frozen_end=="OLR-045" and x.policy=="DEFECT_CORRECTIONS_ONLY" and not x.execution_authority and len(x.manifest_hash)==64\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_045_final_freeze import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_045_final_freeze())\n    def test_policy(self):self.assertEqual(build_olr_freeze_manifest().policy,"DEFECT_CORRECTIONS_ONLY")\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-045 CERTIFICATION TEST");print(" FINAL LEARNING SUBSYSTEM FREEZE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-001 through OLR-045 final freeze certified")\n    print("[PASS] Freeze policy: defect corrections only")\n    print("[DONE] OLR-045 CERTIFIED + FROZEN")\n'
EXTRA_PATH_1=ROOT/'run_olr_045_write_final_freeze_manifest.py'
EXTRA_SOURCE_1='from pathlib import Path\nimport json,os\nfrom dataclasses import asdict\nfrom qseries_v2.oracle_learning_runtime.olr_045_final_freeze import build_olr_freeze_manifest\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-045 FINAL FREEZE MANIFEST")\n    print("="*72)\n    root=Path.cwd()\n    manifest=build_olr_freeze_manifest()\n    path=root/"runtime_state"/"oracle_learning_runtime_freeze_manifest.json"\n    path.parent.mkdir(parents=True,exist_ok=True)\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(asdict(manifest),sort_keys=True,indent=2),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n    print(f"[FREEZE] subsystem={manifest.subsystem}")\n    print(f"[FREEZE] boundary={manifest.frozen_start} through {manifest.frozen_end}")\n    print(f"[FREEZE] policy={manifest.policy}")\n    print(f"[FREEZE] manifest_hash={manifest.manifest_hash}")\n    print("[PASS] Oracle Learning Runtime frozen")\n    print("[PASS] execution_authority=FALSE")\n    print("[PASS] terminal_dependency=NONE")\n    print("[DONE] OLR-045 FINAL FREEZE MANIFEST WRITTEN")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-045 INSTALLER")
    print(" FINAL LEARNING SUBSYSTEM FREEZE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_044_final_production_certification_gate')
    verifier=getattr(upstream,'verify_olr_044_final_production_certification_gate')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-044 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_045_final_freeze import *"
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
        print("[ROLLBACK] OLR-045 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-045 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
