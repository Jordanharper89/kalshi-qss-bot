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

BUILD_ID='OAD-029'
TITLE='ORACLE RUNTIME ADAPTER HEALTH + LATENCY SUPERVISION'
REVISION='OAD_029_PRODUCTION_V1'
MODULE=PACKAGE/'oad_029_runtime_health.py'
TEST=ROOT/'test_oad_029_oracle_runtime_adapter_health_latency_supervision.py'
EXPORTS=('OAD_029_BUILD_ID', 'OAD_029_REVISION', 'KalshiRuntimeHealth', 'evaluate_runtime_health', 'verify_oad_029_oracle_runtime_adapter_health_latency_supervision')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\n\nOAD_029_BUILD_ID="OAD-029"\nOAD_029_REVISION="OAD_029_ORACLE_RUNTIME_ADAPTER_HEALTH_LATENCY_SUPERVISION_V1"\n\n@dataclass(frozen=True)\nclass KalshiRuntimeHealth:\n    connected:bool\n    subscribed:bool\n    live_event_age_ms:float\n    p95_latency_ms:float\n    persistence_ready:bool\n    status:str\n\ndef evaluate_runtime_health(connected,subscribed,live_event_age_ms,p95_latency_ms,persistence_ready,\n                            max_event_age_ms=1000.0,max_p95_latency_ms=250.0):\n    age=float(live_event_age_ms); p95=float(p95_latency_ms)\n    if age<0 or p95<0: raise ValueError("non-negative health metrics required")\n    if not connected: status="DOWN"\n    elif not subscribed: status="DEGRADED"\n    elif not persistence_ready: status="PERSISTENCE_BLOCKED"\n    elif age>max_event_age_ms: status="STALE"\n    elif p95>max_p95_latency_ms: status="LAGGING"\n    else: status="LIVE_READY"\n    return KalshiRuntimeHealth(bool(connected),bool(subscribed),age,p95,bool(persistence_ready),status)\n\ndef verify_oad_029_oracle_runtime_adapter_health_latency_supervision():\n    x=evaluate_runtime_health(True,True,50,25,True)\n    return x.status=="LIVE_READY"\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_029_runtime_health import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_029_oracle_runtime_adapter_health_latency_supervision())\n    def test_stale(self): self.assertEqual(evaluate_runtime_health(True,True,1200,20,True).status,"STALE")\n    def test_persistence(self): self.assertEqual(evaluate_runtime_health(True,True,10,10,False).status,"PERSISTENCE_BLOCKED")\nif __name__=="__main__":\n    print("="*72);print(" OAD-029 CERTIFICATION TEST");print(" ORACLE RUNTIME ADAPTER HEALTH + LATENCY SUPERVISION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Kalshi runtime adapter health/latency supervision certified");print("[DONE] OAD-029 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_028_live_shadow_binding.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_028_live_shadow_binding')
        if getattr(m,'verify_oad_028_live_shadow_postgres_persistence_binding')() is not True:
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
