from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-045'
TITLE='FULL-UNIVERSE LIVE INTELLIGENCE CAPABILITY GATE'
REVISION='OAD_045_PRODUCTION_V1'
MODULE=PACKAGE/'oad_045_full_universe_intelligence_gate.py'
TEST=ROOT/'test_oad_045_full_universe_live_intelligence_capability_gate.py'
EXPORTS=('OAD_045_BUILD_ID', 'OAD_045_REVISION', 'FullUniverseLiveIntelligenceCertification', 'certify_oad_041_through_045', 'verify_oad_045_full_universe_live_intelligence_capability_gate')
MODULE_SOURCE='from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .oad_041_full_universe_partitioning import verify_oad_041_full_universe_stream_partition_expansion\nfrom .oad_042_partitioned_persistence import verify_oad_042_partitioned_persistent_canonical_persistence\nfrom .oad_043_dynamic_intelligence_fanout import verify_oad_043_dynamic_surveillance_fanout\nfrom .oad_044_downstream_intelligence_fanout import verify_oad_044_downstream_intelligence_fanout\n\nOAD_045_BUILD_ID="OAD-045"\nOAD_045_REVISION="OAD_045_FULL_UNIVERSE_LIVE_INTELLIGENCE_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass FullUniverseLiveIntelligenceCertification:\n    builds:tuple[str,...]\n    capability:str\n    runtime_command:str\n    next_capability:str\n    certification_hash:str\n    certified:bool=True\n\ndef certify_oad_041_through_045():\n    checks=(\n        verify_oad_041_full_universe_stream_partition_expansion(),\n        verify_oad_042_partitioned_persistent_canonical_persistence(),\n        verify_oad_043_dynamic_surveillance_fanout(),\n        verify_oad_044_downstream_intelligence_fanout(),\n    )\n    if not all(checks):\n        raise RuntimeError("OAD-041 through OAD-045 certification failed")\n    builds=tuple("OAD-%03d"%i for i in range(41,46))\n    capability="full_universe_partitioned_persistence_surveillance_routing_downstream_intelligence_fanout"\n    next_capability="physical_multi_partition_runtime_and_live_full_universe_coverage_verification"\n    h=sha256(json.dumps({"builds":builds,"capability":capability,"next":next_capability},sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return FullUniverseLiveIntelligenceCertification(builds,capability,"run_oracle_LIVE.py",next_capability,h,True)\n\ndef verify_oad_045_full_universe_live_intelligence_capability_gate():\n    c=certify_oad_041_through_045()\n    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_045_full_universe_intelligence_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_045_full_universe_live_intelligence_capability_gate())\n    def test_five(self):\n        self.assertEqual(len(certify_oad_041_through_045().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OAD-045 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-041 through OAD-045 full-universe live intelligence capability certified")\n    print("[PASS] Next capability: physical multi-partition runtime + live full-universe coverage verification")\n    print("[DONE] OAD-045 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_044_downstream_intelligence_fanout')
        if getattr(m,'verify_oad_044_downstream_intelligence_fanout')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*72)
    print("[BOOT] Revision: "+REVISION)
    print("[ROOT] "+str(ROOT))
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

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
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
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
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise

    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
