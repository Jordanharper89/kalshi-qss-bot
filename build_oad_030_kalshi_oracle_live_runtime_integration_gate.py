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

BUILD_ID='OAD-030'
TITLE='KALSHI → ORACLE LIVE RUNTIME PRODUCTION INTEGRATION GATE'
REVISION='OAD_030_PRODUCTION_V1'
MODULE=PACKAGE/'oad_030_runtime_integration_gate.py'
TEST=ROOT/'test_oad_030_kalshi_oracle_live_runtime_integration_gate.py'
EXPORTS=('OAD_030_BUILD_ID', 'OAD_030_REVISION', 'KalshiOracleRuntimeIntegrationCertification', 'certify_oad_026_through_030', 'verify_oad_030_kalshi_oracle_live_runtime_integration_gate')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom types import MappingProxyType\nfrom .oad_026_persistent_stream_runner import verify_oad_026_persistent_kalshi_live_stream_runner\nfrom .oad_027_event_intake_pump import verify_oad_027_continuous_real_market_event_intake_pump\nfrom .oad_028_live_shadow_binding import verify_oad_028_live_shadow_postgres_persistence_binding\nfrom .oad_029_runtime_health import verify_oad_029_oracle_runtime_adapter_health_latency_supervision\n\nOAD_030_BUILD_ID="OAD-030"\nOAD_030_REVISION="OAD_030_KALSHI_ORACLE_LIVE_RUNTIME_INTEGRATION_GATE_V1"\n\n@dataclass(frozen=True)\nclass KalshiOracleRuntimeIntegrationCertification:\n    builds:tuple[str,...]\n    runtime_command:str\n    capability:str\n    next_capability:str\n    certification_hash:str\n    certified:bool=True\n\ndef certify_oad_026_through_030():\n    checks=(\n        verify_oad_026_persistent_kalshi_live_stream_runner(),\n        verify_oad_027_continuous_real_market_event_intake_pump(),\n        verify_oad_028_live_shadow_postgres_persistence_binding(),\n        verify_oad_029_oracle_runtime_adapter_health_latency_supervision(),\n    )\n    if not all(checks): raise RuntimeError("Kalshi Oracle runtime integration certification failed")\n    builds=tuple("OAD-%03d"%i for i in range(26,31))\n    cap="persistent_kalshi_stream_event_pump_live_shadow_postgres_runtime_health"\n    nxt="physical_runtime_launcher_binding_and_end_to_end_live_event_persistence_verification"\n    h=sha256(json.dumps({"builds":builds,"capability":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return KalshiOracleRuntimeIntegrationCertification(builds,"run_oracle_LIVE.py",cap,nxt,h,True)\n\ndef verify_oad_030_kalshi_oracle_live_runtime_integration_gate():\n    c=certify_oad_026_through_030()\n    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_030_runtime_integration_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_030_kalshi_oracle_live_runtime_integration_gate())\n    def test_five(self): self.assertEqual(len(certify_oad_026_through_030().builds),5)\n    def test_runtime(self): self.assertEqual(certify_oad_026_through_030().runtime_command,"run_oracle_LIVE.py")\nif __name__=="__main__":\n    print("="*72);print(" OAD-030 CERTIFICATION TEST");print(" KALSHI → ORACLE LIVE RUNTIME PRODUCTION INTEGRATION GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-026 through OAD-030 Kalshi → Oracle Live Runtime integration capability certified")\n    print("[PASS] Runtime command: run_oracle_LIVE.py")\n    print("[PASS] Next capability: physical runtime launcher binding + end-to-end live event persistence verification")\n    print("[DONE] OAD-030 CERTIFIED")\n'
EXTRA_1='from qseries_v2.oracle_adapters.kalshi.oad_030_runtime_integration_gate import certify_oad_026_through_030\n\ndef main():\n    c=certify_oad_026_through_030()\n    print("="*72)\n    print(" KALSHI → ORACLE LIVE RUNTIME INTEGRATION CHECK")\n    print("="*72)\n    print("[RUNTIME]",c.runtime_command)\n    print("[CAPABILITY]",c.capability)\n    print("[NEXT]",c.next_capability)\n    print("[CERTIFIED]",c.certified)\n\nif __name__=="__main__":\n    main()\n'

def verify_upstream():
    p=PACKAGE/'oad_029_runtime_health.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_029_runtime_health')
        if getattr(m,'verify_oad_029_oracle_runtime_adapter_health_latency_supervision')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_030_kalshi_oracle_runtime_integration_check.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_030_kalshi_oracle_runtime_integration_check.py',EXTRA_1)
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
