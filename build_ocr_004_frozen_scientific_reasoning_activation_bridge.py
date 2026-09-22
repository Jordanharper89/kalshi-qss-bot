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

BUILD_ID='OCR-004'
TITLE='FROZEN SCIENTIFIC REASONING ACTIVATION BRIDGE'
REVISION='OCR_004_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_004_reasoning_activation_bridge.py'
TEST=ROOT/'test_ocr_004_frozen_scientific_reasoning_activation_bridge.py'
EXPORTS=('OCR_004_BUILD_ID', 'OCR_004_REVISION', 'ScientificReasoningActivationEnvelope', 'build_scientific_reasoning_activation_envelope', 'verify_ocr_004_frozen_scientific_reasoning_activation_bridge')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport importlib,json\n\nOCR_004_BUILD_ID="OCR-004"\nOCR_004_REVISION="OCR_004_FROZEN_SCIENTIFIC_REASONING_ACTIVATION_BRIDGE_V1"\n\ndef _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n\n@dataclass(frozen=True)\nclass ScientificReasoningActivationEnvelope:\n    batch_hash:str\n    observation_count:int\n    market_count:int\n    frozen_reasoning_boundary:str\n    frozen_state_boundary:str\n    reasoning_ready:bool\n    execution_authority:bool\n    envelope_hash:str\n\ndef build_scientific_reasoning_activation_envelope(batch):\n    osr=importlib.import_module("qseries_v2.oracle_scientific_reasoning.osr_030_final_freeze")\n    ois=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    if getattr(osr,"verify_osr_030_scientific_reasoning_final_certification_freeze")() is not True:\n        raise RuntimeError("OSR-030 frozen boundary failed")\n    if getattr(ois,"verify_ois_055_final_production_certification_freeze")() is not True:\n        raise RuntimeError("OIS-055 frozen boundary failed")\n    if not getattr(batch,"read_only",False) or getattr(batch,"observation_count",0)<1:\n        raise ValueError("certified read-only reasoning batch required")\n    raw={"batch_hash":batch.batch_hash,"observation_count":batch.observation_count,"market_count":batch.market_count,\n         "frozen_reasoning_boundary":"OSR-030","frozen_state_boundary":"OIS-055","reasoning_ready":True,"execution_authority":False}\n    return ScientificReasoningActivationEnvelope(raw["batch_hash"],raw["observation_count"],raw["market_count"],\n        raw["frozen_reasoning_boundary"],raw["frozen_state_boundary"],True,False,_h(raw))\n\ndef verify_ocr_004_frozen_scientific_reasoning_activation_bridge():\n    from .ocr_003_reasoning_input_batch import assemble_reasoning_input_batch\n    b=assemble_reasoning_input_batch(({"observation_id":"o1","payload":{"market_ticker":"A","event_type":"ticker"}},))\n    e=build_scientific_reasoning_activation_envelope(b)\n    return e.reasoning_ready and not e.execution_authority and e.frozen_reasoning_boundary=="OSR-030"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_004_reasoning_activation_bridge import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ocr_004_frozen_scientific_reasoning_activation_bridge())\n    def test_no_execution(self): self.assertFalse(verify_ocr_004_frozen_scientific_reasoning_activation_bridge() is False)\nif __name__=="__main__":\n    print("="*72);print(" OCR-004 CERTIFICATION TEST");print(" FROZEN SCIENTIFIC REASONING ACTIVATION BRIDGE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Live reasoning batches admitted to frozen OSR/OIS boundaries read-only")\n    print("[DONE] OCR-004 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_003_reasoning_input_batch')
        if getattr(m,'verify_ocr_003_reasoning_input_batch_assembly')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)

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
