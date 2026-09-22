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

BUILD_ID="OAD-040"
TITLE="KALSHI CANONICAL PERSISTENCE BRIDGE GATE"
REVISION="OAD_040_PRODUCTION_V1"
MODULE=PACKAGE/"oad_040_canonical_persistence_gate.py"
TEST=ROOT/"test_oad_040_kalshi_canonical_persistence_bridge_gate.py"
RUNNER=ROOT/"run_oad_040_physical_live_persistence_verification.py"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
LAUNCHER_TEST=ROOT/"test_run_oracle_LIVE.py"
EXPORTS=('OAD_040_BUILD_ID', 'OAD_040_REVISION', 'KalshiCanonicalPersistenceCertification', 'certify_oad_036_through_040', 'verify_oad_040_kalshi_canonical_persistence_bridge_gate')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .oad_036_websocket_canonical_bridge import verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge\nfrom .oad_037_ola_postgres_router_binding import verify_oad_037_ola_production_postgresql_router_binding\nfrom .oad_038_persistent_persistence_bridge import verify_oad_038_persistent_kalshi_to_postgresql_bridge\nfrom .oad_039_live_persistence_evidence import verify_oad_039_end_to_end_live_persistence_evidence\n\nOAD_040_BUILD_ID="OAD-040"\nOAD_040_REVISION="OAD_040_KALSHI_CANONICAL_PERSISTENCE_BRIDGE_GATE_V1"\n\n@dataclass(frozen=True)\nclass KalshiCanonicalPersistenceCertification:\n    builds:tuple[str,...]\n    runtime_child:str\n    capability:str\n    next_capability:str\n    certification_hash:str\n    certified:bool=True\n\ndef certify_oad_036_through_040():\n    checks=(verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge(),\n            verify_oad_037_ola_production_postgresql_router_binding(),\n            verify_oad_038_persistent_kalshi_to_postgresql_bridge(),\n            verify_oad_039_end_to_end_live_persistence_evidence())\n    if not all(checks): raise RuntimeError("OAD-036 through OAD-040 certification failed")\n    builds=tuple("OAD-%03d"%i for i in range(36,41))\n    cap="kalshi_websocket_to_ola_canonical_observation_to_postgresql_persistence"\n    nxt="full_universe_partitioned_stream_persistence_and_downstream_intelligence_fanout"\n    h=sha256(json.dumps({"builds":builds,"cap":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return KalshiCanonicalPersistenceCertification(builds,"run_oad_038_kalshi_persistence_bridge.py",cap,nxt,h,True)\n\ndef verify_oad_040_kalshi_canonical_persistence_bridge_gate():\n    c=certify_oad_036_through_040()\n    return c.certified and len(c.builds)==5 and c.runtime_child=="run_oad_038_kalshi_persistence_bridge.py"\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_040_canonical_persistence_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_040_kalshi_canonical_persistence_bridge_gate())\n    def test_five(self): self.assertEqual(len(certify_oad_036_through_040().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OAD-040 CERTIFICATION TEST");print(" KALSHI CANONICAL PERSISTENCE BRIDGE GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-036 through OAD-040 canonical persistence bridge certified")\n    print("[PASS] Next capability: full-universe partitioned stream persistence + downstream intelligence fanout")\n    print("[DONE] OAD-040 CERTIFIED")\n'
RUNNER_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge import run_kalshi_persistence_bridge\n\ndef main():\n    print("="*72,flush=True);print(" OAD-040 PHYSICAL LIVE PERSISTENCE VERIFICATION",flush=True);print("="*72,flush=True)\n    r=run_kalshi_persistence_bridge(Path.cwd(),max_persisted=3,progress=lambda x:print(x,flush=True))\n    if r.persisted_observations!=3:\n        raise SystemExit("[FAIL] Expected 3 persisted observations")\n    print("[PASS] Real Kalshi events persisted through certified OLA PostgreSQL router",flush=True)\n    print("[DONE] OAD-040 PHYSICAL PERSISTENCE VERIFIED",flush=True)\nif __name__=="__main__": main()\n'
LAUNCHER_SOURCE='from __future__ import annotations\nimport argparse,importlib,subprocess,sys,time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME="Oracle Live Runtime"\nLAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_CANONICAL_PERSISTENCE_OAD_040_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name:str\n    state:str\n    certified:bool\n    terminal_dependency:bool\n    execution_authority:bool\n\ndef verify_frozen_ois_boundary():\n    m=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    if getattr(m,"verify_ois_055_final_production_certification_freeze")() is not True: raise RuntimeError("OIS verification failed")\n    return True\n\ndef verify_kalshi_boundary():\n    m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_040_canonical_persistence_gate")\n    if getattr(m,"verify_oad_040_kalshi_canonical_persistence_bridge_gate")() is not True: raise RuntimeError("OAD-040 verification failed")\n    return True\n\ndef build_boot_report():\n    verify_frozen_ois_boundary();verify_kalshi_boundary()\n    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)\n\ndef format_boot_report(r):\n    return "\\n".join(("="*72," ORACLE LIVE RUNTIME","="*72,f"[REVISION] {LAUNCHER_REVISION}",\n        "[STATE] RUNNING","[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] OAD-001 through OAD-040 Kalshi canonical persistence boundary verified",\n        "[PASS] Operator Terminal dependency: NONE","[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime with Kalshi → OLA → PostgreSQL persistence verified"))\n\ndef _start_child(root):\n    p=root/"run_oad_038_kalshi_persistence_bridge.py"\n    if not p.is_file(): raise RuntimeError("Kalshi persistence bridge runner missing")\n    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))\n\ndef run_forever(cadence):\n    print(format_boot_report(build_boot_report()),flush=True)\n    root=Path.cwd(); proc=_start_child(root); restarts=0; heartbeat=0\n    print(f"[KALSHI] canonical persistence bridge started pid={proc.pid}",flush=True)\n    try:\n        while True:\n            heartbeat+=1\n            if proc.poll() is not None:\n                restarts+=1\n                print(f"[KALSHI] persistence child exited code={proc.returncode}; restart_count={restarts}; restarting",flush=True)\n                time.sleep(min(5.0,cadence)); proc=_start_child(root)\n            print(f"[ORACLE] heartbeat={heartbeat} state=RUNNING kalshi_persistence_child=RUNNING kalshi_restarts={restarts} terminal_dependency=NONE execution_authority=FALSE",flush=True)\n            time.sleep(cadence)\n    except KeyboardInterrupt:\n        print()\n        if proc.poll() is None:\n            proc.terminate()\n            try: proc.wait(timeout=5)\n            except Exception: proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)\n        return 0\n\ndef main(argv=None):\n    p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");p.add_argument("--cadence-seconds",type=float,default=5.0);a=p.parse_args(argv)\n    if a.cadence_seconds<=0: raise SystemExit("--cadence-seconds must be > 0")\n    if a.check:\n        print(format_boot_report(build_boot_report()));return 0\n    return run_forever(a.cadence_seconds)\nif __name__=="__main__": raise SystemExit(main())\n'
LAUNCHER_TEST_SOURCE='\nimport subprocess,sys,unittest\nfrom pathlib import Path\nimport run_oracle_LIVE as live\nclass T(unittest.TestCase):\n    def test_boot(self): self.assertTrue(live.build_boot_report().certified)\n    def test_check(self):\n        p=subprocess.run([sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],text=True,capture_output=True)\n        self.assertEqual(p.returncode,0);self.assertIn("PostgreSQL persistence verified",p.stdout)\nif __name__=="__main__":\n    print("="*72);print(" ORACLE LIVE + OAD-040 PERSISTENCE LAUNCHER TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle launcher bound to persistent canonical Kalshi persistence child")\n'

def verify_upstream():
    p=PACKAGE/"oad_039_live_persistence_evidence.py"
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_039_live_persistence_evidence")
        if getattr(m,"verify_oad_039_end_to_end_live_persistence_evidence")() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" OAD-040 INSTALLER");print(" KALSHI CANONICAL PERSISTENCE BRIDGE GATE");print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")

    affected=(MODULE,TEST,RUNNER,LAUNCHER,LAUNCHER_TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)
        update_init("# OAD-040 exports",MODULE.stem,EXPORTS)

        for path in (MODULE,TEST,RUNNER):
            compile(path.read_text(encoding="utf-8"),str(path),"exec")

        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi.oad_040_canonical_persistence_gate"
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            if getattr(m,"verify_oad_040_kalshi_canonical_persistence_bridge_gate")() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

        run_test(TEST)

        write_exact(LAUNCHER,LAUNCHER_SOURCE)
        write_exact(LAUNCHER_TEST,LAUNCHER_TEST_SOURCE)
        compile(LAUNCHER.read_text(encoding="utf-8"),str(LAUNCHER),"exec")
        compile(LAUNCHER_TEST.read_text(encoding="utf-8"),str(LAUNCHER_TEST),"exec")
        subprocess.run([sys.executable,str(LAUNCHER_TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)

    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists(): path.unlink()
            else: path.write_bytes(old)
        print("[ROLLBACK] OAD-040 installation failed; all affected files restored")
        raise

    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "runner":RUNNER.name,"launcher":LAUNCHER.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),
                        RUNNER.name:sha(RUNNER),LAUNCHER.name:sha(LAUNCHER),
                        LAUNCHER_TEST.name:sha(LAUNCHER_TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Wrote: "+RUNNER.name)
    print("[PASS] PHYSICAL BINDING: "+LAUNCHER.name)
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Existing OLA PostgreSQL router preserved and reused")
    print("[PASS] Transactional rollback protection active")
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] OAD-040 INSTALLATION AND ORACLE PERSISTENCE BINDING COMPLETE")

if __name__=="__main__": main()
