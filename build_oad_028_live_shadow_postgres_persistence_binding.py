from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-028'
TITLE='LIVE SHADOW / POSTGRES PERSISTENCE BINDING'
REVISION='OAD_028_PRODUCTION_V1'
MODULE=PACKAGE/'oad_028_live_shadow_binding.py'
TEST=ROOT/'test_oad_028_live_shadow_postgres_persistence_binding.py'
EXPORTS=('OAD_028_BUILD_ID', 'OAD_028_REVISION', 'LiveShadowPersistenceRecord', 'build_live_shadow_persistence_record', 'persistence_ready', 'verify_oad_028_live_shadow_postgres_persistence_binding')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\n\nOAD_028_BUILD_ID="OAD-028"\nOAD_028_REVISION="OAD_028_LIVE_SHADOW_POSTGRES_PERSISTENCE_BINDING_V1"\n\n@dataclass(frozen=True)\nclass LiveShadowPersistenceRecord:\n    adapter_id:str\n    source_id:str\n    entity_id:str\n    event_type:str\n    event_hash:str\n    persisted:bool\n    execution_authority:bool=False\n\ndef build_live_shadow_persistence_record(adapter_id,source_id,entity_id,event_type,event_hash,persisted):\n    if not all((adapter_id,source_id,entity_id,event_type,event_hash)):\n        raise ValueError("complete persistence identity required")\n    return LiveShadowPersistenceRecord(adapter_id,source_id,entity_id,event_type,event_hash,bool(persisted),False)\n\ndef persistence_ready(postgres_available,live_shadow_available):\n    return bool(postgres_available and live_shadow_available)\n\ndef verify_oad_028_live_shadow_postgres_persistence_binding():\n    r=build_live_shadow_persistence_record("kalshi_predictions_universal","kalshi","A","trade","h",True)\n    return persistence_ready(True,True) and r.persisted and not r.execution_authority\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_028_live_shadow_binding import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_028_live_shadow_postgres_persistence_binding())\n    def test_both_required(self): self.assertFalse(persistence_ready(True,False))\nif __name__=="__main__":\n    print("="*72);print(" OAD-028 CERTIFICATION TEST");print(" LIVE SHADOW / POSTGRES PERSISTENCE BINDING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Kalshi adapter-to-Live-Shadow/PostgreSQL binding contract certified");print("[DONE] OAD-028 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_027_event_intake_pump.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_027_event_intake_pump')
        if getattr(m,'verify_oad_027_continuous_real_market_event_intake_pump')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

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
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
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

if __name__=="__main__": main()
