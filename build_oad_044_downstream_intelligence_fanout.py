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

BUILD_ID='OAD-044'
TITLE='DOWNSTREAM INTELLIGENCE FANOUT'
REVISION='OAD_044_PRODUCTION_V1'
MODULE=PACKAGE/'oad_044_downstream_intelligence_fanout.py'
TEST=ROOT/'test_oad_044_downstream_intelligence_fanout.py'
EXPORTS=('OAD_044_BUILD_ID', 'OAD_044_REVISION', 'DEFAULT_CONSUMERS', 'DownstreamIntelligenceEnvelope', 'build_downstream_intelligence_envelope', 'verify_oad_044_downstream_intelligence_fanout')
MODULE_SOURCE='from dataclasses import dataclass\nOAD_044_BUILD_ID="OAD-044"\nOAD_044_REVISION="OAD_044_DOWNSTREAM_INTELLIGENCE_FANOUT_V1"\nDEFAULT_CONSUMERS=("observation_intelligence","universal_market_discovery","oracle_memory")\n\n@dataclass(frozen=True)\nclass DownstreamIntelligenceEnvelope:\n    observation_id:str\n    source_id:str\n    market_ticker:str\n    event_type:str\n    surveillance_tier:str\n    consumers:tuple[str,...]\n    blocking:bool=False\n    execution_authority:bool=False\n\ndef build_downstream_intelligence_envelope(observation,market_ticker,event_type,surveillance_tier,consumers=DEFAULT_CONSUMERS):\n    oid=str(getattr(observation,"observation_id","")).strip()\n    source=str(getattr(observation,"source_id","")).strip()\n    if not oid or not source:\n        raise ValueError("observation identity required")\n    consumers=tuple(str(x) for x in consumers if str(x))\n    if not consumers:\n        raise ValueError("consumers required")\n    return DownstreamIntelligenceEnvelope(\n        oid,source,str(market_ticker),str(event_type),str(surveillance_tier).upper(),consumers,False,False\n    )\n\ndef verify_oad_044_downstream_intelligence_fanout():\n    class O:\n        observation_id="x"\n        source_id="source.kalshi.market_data"\n    e=build_downstream_intelligence_envelope(O(),"A","ticker","HOT")\n    return e.consumers==DEFAULT_CONSUMERS and not e.blocking and not e.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_044_downstream_intelligence_fanout import *\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_044_downstream_intelligence_fanout())\nif __name__=="__main__":\n    print("="*72);print(" OAD-044 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Downstream intelligence fanout certified")\n    print("[DONE] OAD-044 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_043_dynamic_intelligence_fanout')
        if getattr(m,'verify_oad_043_dynamic_surveillance_fanout')() is not True:
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
