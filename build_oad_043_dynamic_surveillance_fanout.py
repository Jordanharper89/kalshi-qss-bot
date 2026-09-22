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

BUILD_ID='OAD-043'
TITLE='DYNAMIC HOT / ACTIVE / BROAD-SURVEILLANCE FANOUT'
REVISION='OAD_043_PRODUCTION_V1'
MODULE=PACKAGE/'oad_043_dynamic_intelligence_fanout.py'
TEST=ROOT/'test_oad_043_dynamic_surveillance_fanout.py'
EXPORTS=('OAD_043_BUILD_ID', 'OAD_043_REVISION', 'IntelligenceFanoutDecision', 'route_intelligence_fanout', 'verify_oad_043_dynamic_surveillance_fanout')
MODULE_SOURCE='from dataclasses import dataclass\nOAD_043_BUILD_ID="OAD-043"\nOAD_043_REVISION="OAD_043_DYNAMIC_SURVEILLANCE_FANOUT_V1"\n\n@dataclass(frozen=True)\nclass IntelligenceFanoutDecision:\n    market_ticker:str\n    surveillance_tier:str\n    acquisition_lane:str\n    intelligence_lane:str\n    priority:int\n\ndef route_intelligence_fanout(market_ticker,surveillance_tier):\n    tier=str(surveillance_tier).upper()\n    mapping={\n        "ULTRA_HOT":("FAST_PATH","IMMEDIATE",100),\n        "HOT":("FAST_PATH","IMMEDIATE",90),\n        "ACTIVE":("FAST_PATH","STANDARD",70),\n        "WARM":("BROAD_SURVEILLANCE","BACKGROUND",40),\n        "COLD":("BROAD_SURVEILLANCE","BACKGROUND",20),\n        "DORMANT":("BROAD_SURVEILLANCE","BACKGROUND",10),\n        "DEAD":("ARCHIVE","ARCHIVE",0),\n    }\n    if tier not in mapping:\n        raise ValueError("unknown surveillance tier")\n    acquisition,intelligence,priority=mapping[tier]\n    return IntelligenceFanoutDecision(str(market_ticker),tier,acquisition,intelligence,priority)\n\ndef verify_oad_043_dynamic_surveillance_fanout():\n    return route_intelligence_fanout("A","HOT").priority==90 and route_intelligence_fanout("B","DEAD").priority==0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_043_dynamic_intelligence_fanout import *\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_043_dynamic_surveillance_fanout())\nif __name__=="__main__":\n    print("="*72);print(" OAD-043 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Dynamic surveillance fanout certified")\n    print("[DONE] OAD-043 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_042_partitioned_persistence')
        if getattr(m,'verify_oad_042_partitioned_persistent_canonical_persistence')() is not True:
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
