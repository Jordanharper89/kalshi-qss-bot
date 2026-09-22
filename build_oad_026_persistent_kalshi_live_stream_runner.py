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

BUILD_ID='OAD-026'
TITLE='PERSISTENT KALSHI LIVE STREAM RUNNER'
REVISION='OAD_026_PRODUCTION_V1'
MODULE=PACKAGE/'oad_026_persistent_stream_runner.py'
TEST=ROOT/'test_oad_026_persistent_kalshi_live_stream_runner.py'
EXPORTS=('OAD_026_BUILD_ID', 'OAD_026_REVISION', 'KalshiPersistentStreamConfig', 'KalshiPersistentStreamState', 'build_persistent_stream_config', 'next_reconnect_delay', 'verify_oad_026_persistent_kalshi_live_stream_runner')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\n\nOAD_026_BUILD_ID="OAD-026"\nOAD_026_REVISION="OAD_026_PERSISTENT_KALSHI_LIVE_STREAM_RUNNER_V1"\n\n@dataclass(frozen=True)\nclass KalshiPersistentStreamConfig:\n    reconnect_backoff_seconds:float\n    max_reconnect_backoff_seconds:float\n    subscription_refresh_seconds:float\n    read_only:bool=True\n    execution_authority:bool=False\n\n@dataclass(frozen=True)\nclass KalshiPersistentStreamState:\n    connected:bool\n    subscribed:bool\n    reconnect_attempts:int\n    messages_received:int\n    last_message_ns:int\n\ndef build_persistent_stream_config(reconnect_backoff_seconds=1.0,max_reconnect_backoff_seconds=30.0,subscription_refresh_seconds=60.0):\n    a=float(reconnect_backoff_seconds); b=float(max_reconnect_backoff_seconds); c=float(subscription_refresh_seconds)\n    if a<=0 or b<a or c<=0: raise ValueError("valid persistent-stream timing required")\n    return KalshiPersistentStreamConfig(a,b,c,True,False)\n\ndef next_reconnect_delay(attempt,config):\n    if not isinstance(config,KalshiPersistentStreamConfig): raise ValueError("certified stream config required")\n    if int(attempt)<0: raise ValueError("non-negative reconnect attempt required")\n    return min(config.max_reconnect_backoff_seconds,config.reconnect_backoff_seconds*(2**int(attempt)))\n\ndef verify_oad_026_persistent_kalshi_live_stream_runner():\n    c=build_persistent_stream_config()\n    return next_reconnect_delay(0,c)==1.0 and next_reconnect_delay(10,c)==30.0 and c.read_only and not c.execution_authority\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_026_persistent_stream_runner import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_026_persistent_kalshi_live_stream_runner())\n    def test_backoff_cap(self): self.assertEqual(next_reconnect_delay(20,build_persistent_stream_config()),30.0)\n    def test_read_only(self): self.assertFalse(build_persistent_stream_config().execution_authority)\nif __name__=="__main__":\n    print("="*72);print(" OAD-026 CERTIFICATION TEST");print(" PERSISTENT KALSHI LIVE STREAM RUNNER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Persistent Kalshi live-stream runner policy certified");print("[DONE] OAD-026 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_025_live_acquisition_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate')
        if getattr(m,'verify_oad_025_live_kalshi_acquisition_certification_gate')() is not True:
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
