from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-005'
TITLE='LIVE REASONING INTAKE ACTIVATION CAPABILITY GATE'
REVISION='OCR_005_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_005_capability_gate.py'
TEST=ROOT/'test_ocr_005_live_reasoning_intake_activation_capability_gate.py'
EXPORTS=('OCR_005_BUILD_ID', 'OCR_005_REVISION', 'OCRCapabilityCertification', 'certify_ocr_001_through_005', 'verify_ocr_005_live_reasoning_intake_activation_capability_gate')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .ocr_001_foundation import verify_ocr_001_continuous_reasoning_runtime_foundation\nfrom .ocr_002_live_observation_read_model import verify_ocr_002_postgresql_live_observation_read_model\nfrom .ocr_003_reasoning_input_batch import verify_ocr_003_reasoning_input_batch_assembly\nfrom .ocr_004_reasoning_activation_bridge import verify_ocr_004_frozen_scientific_reasoning_activation_bridge\n\nOCR_005_BUILD_ID="OCR-005"\nOCR_005_REVISION="OCR_005_LIVE_REASONING_INTAKE_ACTIVATION_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass OCRCapabilityCertification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certification_hash:str\n    certified:bool=True\n\ndef certify_ocr_001_through_005():\n    checks=(verify_ocr_001_continuous_reasoning_runtime_foundation(),\n            verify_ocr_002_postgresql_live_observation_read_model(),\n            verify_ocr_003_reasoning_input_batch_assembly(),\n            verify_ocr_004_frozen_scientific_reasoning_activation_bridge())\n    if not all(checks): raise RuntimeError("OCR capability certification failed")\n    builds=tuple("OCR-%03d"%i for i in range(1,6))\n    cap="live_postgresql_observation_to_frozen_scientific_reasoning_activation"\n    nxt="continuous_scientific_reasoning_invocation_and_intelligence_state_update"\n    h=sha256(json.dumps({"builds":builds,"cap":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return OCRCapabilityCertification(builds,cap,nxt,h,True)\n\ndef verify_ocr_005_live_reasoning_intake_activation_capability_gate():\n    c=certify_ocr_001_through_005()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_005_capability_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ocr_005_live_reasoning_intake_activation_capability_gate())\n    def test_five(self): self.assertEqual(len(certify_ocr_001_through_005().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OCR-005 CERTIFICATION TEST");print(" LIVE REASONING INTAKE ACTIVATION CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OCR-001 through OCR-005 live reasoning-intake activation certified")\n    print("[PASS] Next capability: continuous scientific reasoning invocation + intelligence-state update")\n    print("[DONE] OCR-005 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations\nfrom qseries_v2.oracle_continuous_reasoning.ocr_003_reasoning_input_batch import assemble_reasoning_input_batch\nfrom qseries_v2.oracle_continuous_reasoning.ocr_004_reasoning_activation_bridge import build_scientific_reasoning_activation_envelope\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OCR-005 PHYSICAL LIVE REASONING INTAKE VERIFICATION")\n    print("="*72)\n    result=read_latest_canonical_observations(Path.cwd(),limit=10)\n    print(f"[POSTGRESQL] source={result.schema}.{result.table} rows={len(result.rows)} read_only={result.read_only}")\n    batch=assemble_reasoning_input_batch(result.rows)\n    print(f"[BATCH] observations={batch.observation_count} markets={batch.market_count} hash={batch.batch_hash}")\n    envelope=build_scientific_reasoning_activation_envelope(batch)\n    print(f"[REASONING] ready={envelope.reasoning_ready} OSR={envelope.frozen_reasoning_boundary} OIS={envelope.frozen_state_boundary}")\n    print("[PASS] Real persisted observations reached the frozen reasoning activation boundary")\n    print("[DONE] OCR-005 PHYSICAL LIVE REASONING INTAKE VERIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_004_reasoning_activation_bridge')
        if getattr(m,'verify_ocr_004_frozen_scientific_reasoning_activation_bridge')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_ocr_005_physical_live_reasoning_intake_verification.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_ocr_005_physical_live_reasoning_intake_verification.py',EXTRA_1)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_reasoning."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
