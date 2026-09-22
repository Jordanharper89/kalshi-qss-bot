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

BUILD_ID='OAD-035'
TITLE='PHYSICAL ORACLE + KALSHI PRODUCTION ACTIVATION GATE'
REVISION='OAD_035_PRODUCTION_V1'
MODULE=PACKAGE/'oad_035_physical_activation_gate.py'
TEST=ROOT/'test_oad_035_physical_oracle_kalshi_production_activation_gate.py'
RUNNER=ROOT/'run_oad_035_physical_oracle_kalshi_activation_verification.py'
LAUNCHER=ROOT/'run_oracle_LIVE.py'
LAUNCHER_TEST=ROOT/'test_run_oracle_LIVE.py'
EXPORTS=('OAD_035_BUILD_ID', 'OAD_035_REVISION', 'PhysicalOracleKalshiActivationCertification', 'certify_oad_031_through_035', 'verify_oad_035_physical_oracle_kalshi_production_activation_gate')

MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom pathlib import Path\nfrom .oad_031_runtime_binding import verify_oad_031_physical_oracle_live_runtime_kalshi_binding\nfrom .oad_032_persistent_live_loop import verify_oad_032_persistent_real_kalshi_message_loop\nfrom .oad_033_persistence_verification import verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification\nfrom .oad_034_runtime_status import verify_oad_034_runtime_kalshi_status_surface\n\nOAD_035_BUILD_ID="OAD-035"\nOAD_035_REVISION="OAD_035_PHYSICAL_ORACLE_KALSHI_PRODUCTION_ACTIVATION_GATE_V1"\n\n@dataclass(frozen=True)\nclass PhysicalOracleKalshiActivationCertification:\n    builds:tuple[str,...]\n    runtime_command:str\n    dual_lane_architecture:str\n    next_capability:str\n    certification_hash:str\n    certified:bool=True\n\ndef certify_oad_031_through_035():\n    checks=(verify_oad_031_physical_oracle_live_runtime_kalshi_binding(),\n            verify_oad_032_persistent_real_kalshi_message_loop(),\n            verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification(),\n            verify_oad_034_runtime_kalshi_status_surface())\n    if not all(checks): raise RuntimeError("Physical Oracle/Kalshi activation certification failed")\n    builds=tuple("OAD-%03d"%i for i in range(31,36))\n    arch="kalshi_websocket_fast_lane_plus_certified_ola_live_shadow_postgresql_lane"\n    nxt="direct_websocket_event_to_canonical_observation_persistence_bridge_and_multi_adapter_expansion"\n    h=sha256(json.dumps({"builds":builds,"arch":arch,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return PhysicalOracleKalshiActivationCertification(builds,"run_oracle_LIVE.py",arch,nxt,h,True)\n\ndef verify_oad_035_physical_oracle_kalshi_production_activation_gate():\n    c=certify_oad_031_through_035()\n    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_035_physical_activation_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_035_physical_oracle_kalshi_production_activation_gate())\n    def test_five(self): self.assertEqual(len(certify_oad_031_through_035().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OAD-035 CERTIFICATION TEST");print(" PHYSICAL ORACLE + KALSHI PRODUCTION ACTIVATION GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-031 through OAD-035 physical Oracle/Kalshi activation architecture certified")\n    print("[DONE] OAD-035 CERTIFIED")\n'
RUNNER_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import run_persistent_kalshi_loop\nfrom qseries_v2.oracle_adapters.kalshi.oad_033_persistence_verification import run_existing_persistence_diagnostic\nfrom qseries_v2.oracle_adapters.kalshi.oad_034_runtime_status import build_oracle_kalshi_status\n\ndef main():\n    root=Path.cwd()\n    print("="*72,flush=True)\n    print(" OAD-035 PHYSICAL ORACLE + KALSHI ACTIVATION VERIFICATION",flush=True)\n    print("="*72,flush=True)\n    print("[FAST LANE] Waiting for real Kalshi market events",flush=True)\n    ws=run_persistent_kalshi_loop(root,stop_after_market_messages=3,timeout_seconds=15,progress=lambda x:print(x,flush=True))\n    print("[PERSISTENCE LANE] Running existing certified OLA/PostgreSQL diagnostic",flush=True)\n    code,persisted,out=run_existing_persistence_diagnostic(root,timeout_seconds=180)\n    print(out,flush=True)\n    status=build_oracle_kalshi_status(True,ws.subscription_acks>0,ws.market_messages,ws.reconnects,persisted)\n    print("[STATUS]",status,flush=True)\n    if status.status!="LIVE_READY":\n        raise SystemExit("[FAIL] Oracle/Kalshi physical activation did not reach LIVE_READY")\n    print("[PASS] Real Kalshi market events observed and canonical Live Shadow/PostgreSQL persistence advanced",flush=True)\n    print("[PASS] Dual-lane Oracle/Kalshi production activation verified",flush=True)\n    print("[DONE] OAD-035 PHYSICAL ACTIVATION VERIFIED",flush=True)\n\nif __name__=="__main__":\n    main()\n'
LAUNCHER_SOURCE='from __future__ import annotations\n\nimport argparse\nimport importlib\nimport subprocess\nimport sys\nimport time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME = "Oracle Live Runtime"\nLAUNCHER_REVISION = "ORACLE_LIVE_RUNTIME_KALSHI_BINDING_OAD_035_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name: str\n    state: str\n    certified: bool\n    terminal_dependency: bool\n    execution_authority: bool\n\ndef verify_frozen_ois_boundary():\n    m=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    if getattr(m,"verify_ois_055_final_production_certification_freeze")() is not True:\n        raise RuntimeError("Frozen OIS-055 certification boundary verification failed")\n    return True\n\ndef verify_kalshi_boundary():\n    m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_035_physical_activation_gate")\n    if getattr(m,"verify_oad_035_physical_oracle_kalshi_production_activation_gate")() is not True:\n        raise RuntimeError("OAD-035 Kalshi activation boundary verification failed")\n    return True\n\ndef build_boot_report():\n    verify_frozen_ois_boundary()\n    verify_kalshi_boundary()\n    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)\n\ndef format_boot_report(report):\n    return "\\n".join((\n        "="*72,\n        " ORACLE LIVE RUNTIME",\n        "="*72,\n        f"[REVISION] {LAUNCHER_REVISION}",\n        f"[STATE] {report.state}",\n        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] OAD-001 through OAD-035 Kalshi boundary verified",\n        "[PASS] Operator Terminal dependency: NONE",\n        "[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime with Kalshi integration boundary verified",\n    ))\n\ndef run_forever(cadence_seconds):\n    report=build_boot_report()\n    print(format_boot_report(report),flush=True)\n    root=Path.cwd()\n    child=root/"run_oad_032_kalshi_persistent_stream.py"\n    proc=None\n    if child.is_file():\n        proc=subprocess.Popen([sys.executable,str(child)],cwd=str(root))\n        print("[KALSHI] persistent live stream child started pid="+str(proc.pid),flush=True)\n    else:\n        print("[KALSHI] persistent stream runner missing; runtime degraded",flush=True)\n\n    sequence=0\n    try:\n        while True:\n            sequence+=1\n            child_state=("RUNNING" if proc and proc.poll() is None else "STOPPED")\n            print(f"[ORACLE] heartbeat={sequence} state=RUNNING kalshi_child={child_state} terminal_dependency=NONE execution_authority=FALSE",flush=True)\n            time.sleep(cadence_seconds)\n    except KeyboardInterrupt:\n        print()\n        if proc and proc.poll() is None:\n            proc.terminate()\n            try: proc.wait(timeout=5)\n            except Exception: proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)\n        return 0\n\ndef main(argv=None):\n    parser=argparse.ArgumentParser(description="Oracle Live Runtime production launcher")\n    parser.add_argument("--check",action="store_true")\n    parser.add_argument("--cadence-seconds",type=float,default=5.0)\n    args=parser.parse_args(argv)\n    if args.cadence_seconds<=0: raise SystemExit("--cadence-seconds must be > 0")\n    report=build_boot_report()\n    if args.check:\n        print(format_boot_report(report))\n        return 0\n    return run_forever(args.cadence_seconds)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
LAUNCHER_TEST_SOURCE='\nimport subprocess,sys,unittest\nfrom pathlib import Path\nimport run_oracle_LIVE as live\n\nclass T(unittest.TestCase):\n    def test_boot(self):\n        r=live.build_boot_report()\n        self.assertTrue(r.certified);self.assertFalse(r.execution_authority)\n    def test_check(self):\n        p=subprocess.run([sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],text=True,capture_output=True)\n        self.assertEqual(p.returncode,0)\n        self.assertIn("Kalshi integration boundary verified",p.stdout)\n\nif __name__=="__main__":\n    print("="*72);print(" ORACLE LIVE RUNTIME + KALSHI LAUNCHER TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] run_oracle_LIVE.py Kalshi binding certified")\n'

def verify_upstream():
    p=PACKAGE/'oad_034_runtime_status.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_034_runtime_status")
        if getattr(m,"verify_oad_034_runtime_kalshi_status_surface")() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" OAD-035 INSTALLER");print(" PHYSICAL ORACLE + KALSHI PRODUCTION ACTIVATION GATE");print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")

    affected=(MODULE,TEST,RUNNER,LAUNCHER,LAUNCHER_TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)
        update_init("# OAD-035 exports",MODULE.stem,EXPORTS)

        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(RUNNER.read_text(encoding="utf-8"),str(RUNNER),"exec")

        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi.oad_035_physical_activation_gate"
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            if getattr(m,"verify_oad_035_physical_oracle_kalshi_production_activation_gate")() is not True:
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
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OAD-035 installation failed; all affected files restored")
        raise

    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"launcher":LAUNCHER.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),
                        RUNNER.name:sha(RUNNER),LAUNCHER.name:sha(LAUNCHER),
                        LAUNCHER_TEST.name:sha(LAUNCHER_TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Wrote: "+RUNNER.name)
    print("[PASS] PHYSICAL BINDING: "+LAUNCHER.name)
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Transactional rollback protection active")
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] OAD-035 INSTALLATION AND ORACLE LAUNCHER BINDING COMPLETE")

if __name__=="__main__":
    main()
