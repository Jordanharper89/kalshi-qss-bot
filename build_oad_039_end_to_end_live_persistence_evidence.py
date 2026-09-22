from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
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
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-039'
TITLE='END-TO-END LIVE PERSISTENCE EVIDENCE'
REVISION='OAD_039_PRODUCTION_V1'
MODULE=PACKAGE/'oad_039_live_persistence_evidence.py'
TEST=ROOT/'test_oad_039_end_to_end_live_persistence_evidence.py'
EXPORTS=('OAD_039_BUILD_ID', 'OAD_039_REVISION', 'LivePersistenceEvidence', 'build_live_persistence_evidence', 'verify_oad_039_end_to_end_live_persistence_evidence')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\n\nOAD_039_BUILD_ID="OAD-039"\nOAD_039_REVISION="OAD_039_END_TO_END_LIVE_PERSISTENCE_EVIDENCE_V1"\n\n@dataclass(frozen=True)\nclass LivePersistenceEvidence:\n    market_events:int\n    persisted_observations:int\n    observation_ids:tuple[str,...]\n    complete:bool\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef build_live_persistence_evidence(observation_ids,market_events):\n    ids=tuple(str(x) for x in observation_ids if str(x))\n    events=int(market_events)\n    if events<0: raise ValueError("non-negative market_events required")\n    complete=bool(events>0 and len(ids)==events)\n    return LivePersistenceEvidence(events,len(ids),ids,complete,True,False)\n\ndef verify_oad_039_end_to_end_live_persistence_evidence():\n    x=build_live_persistence_evidence(("a","b","c"),3)\n    return x.complete and x.persisted_observations==3 and not x.execution_authority\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_039_live_persistence_evidence import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_039_end_to_end_live_persistence_evidence())\n    def test_mismatch(self): self.assertFalse(build_live_persistence_evidence(("a",),2).complete)\nif __name__=="__main__":\n    print("="*72);print(" OAD-039 CERTIFICATION TEST");print(" END-TO-END LIVE PERSISTENCE EVIDENCE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Live event-to-persistence evidence contract certified");print("[DONE] OAD-039 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_038_persistent_persistence_bridge.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge')
        if getattr(m,'verify_oad_038_persistent_kalshi_to_postgresql_bridge')() is not True:
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
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True: raise RuntimeError("Production verifier returned false")
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
