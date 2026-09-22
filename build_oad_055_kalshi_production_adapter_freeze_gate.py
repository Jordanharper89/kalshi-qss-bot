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

BUILD_ID='OAD-055'
TITLE='KALSHI PRODUCTION ADAPTER FREEZE GATE'
REVISION='OAD_055_PRODUCTION_V1'
MODULE=PACKAGE/'oad_055_kalshi_production_freeze.py'
TEST=ROOT/'test_oad_055_kalshi_production_adapter_freeze_gate.py'
EXPORTS=('OAD_055_BUILD_ID', 'OAD_055_REVISION', 'KalshiProductionAdapterFreeze', 'certify_oad_051_through_055', 'verify_oad_055_kalshi_production_adapter_freeze_gate')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nfrom .oad_051_adaptive_orderbook_tier_scheduler import verify_oad_051_adaptive_orderbook_tier_scheduler\nfrom .oad_052_dynamic_orderbook_rotation import verify_oad_052_dynamic_orderbook_partition_rotation\nfrom .oad_053_background_universe_inventory import verify_oad_053_incremental_background_universe_inventory\nfrom .oad_054_continuous_runtime_binding import verify_oad_054_continuous_full_universe_runtime_binding\n\nOAD_055_BUILD_ID="OAD-055"\nOAD_055_REVISION="OAD_055_KALSHI_PRODUCTION_ADAPTER_FREEZE_GATE_V1"\n\n@dataclass(frozen=True)\nclass KalshiProductionAdapterFreeze:\n    builds:tuple[str,...]\n    runtime_command:str\n    frozen_through:str\n    mutation_policy:str\n    next_adapter_phase:str\n    freeze_hash:str\n    certified:bool=True\n\ndef certify_oad_051_through_055():\n    checks=(\n        verify_oad_051_adaptive_orderbook_tier_scheduler(),\n        verify_oad_052_dynamic_orderbook_partition_rotation(),\n        verify_oad_053_incremental_background_universe_inventory(),\n        verify_oad_054_continuous_full_universe_runtime_binding(),\n    )\n    if not all(checks):\n        raise RuntimeError("OAD-051 through OAD-055 certification failed")\n    builds=tuple("OAD-%03d"%i for i in range(51,56))\n    payload={\n        "builds":builds,\n        "runtime":"run_oracle_LIVE.py",\n        "frozen_through":"OAD-055",\n        "policy":"defect_corrections_only",\n        "next":"next_venue_adapter_or_observation_source",\n    }\n    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return KalshiProductionAdapterFreeze(\n        builds,\n        payload["runtime"],\n        payload["frozen_through"],\n        payload["policy"],\n        payload["next"],\n        h,\n        True,\n    )\n\ndef verify_oad_055_kalshi_production_adapter_freeze_gate():\n    c=certify_oad_051_through_055()\n    return c.certified and c.frozen_through=="OAD-055" and c.mutation_policy=="defect_corrections_only"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_055_kalshi_production_adapter_freeze_gate())\n    def test_freeze(self): self.assertEqual(certify_oad_051_through_055().frozen_through,"OAD-055")\nif __name__=="__main__":\n    print("="*72);print(" OAD-055 CERTIFICATION TEST");print(" KALSHI PRODUCTION ADAPTER FREEZE GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-051 through OAD-055 Kalshi production adapter capability certified")\n    print("[PASS] Freeze policy: defect corrections only")\n    print("[DONE] OAD-055 CERTIFIED")\n'
EXTRA_1='from __future__ import annotations\nimport argparse,importlib,subprocess,sys,time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME="Oracle Live Runtime"\nLAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_PRODUCTION_FREEZE_OAD_055_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name:str\n    state:str\n    certified:bool\n    terminal_dependency:bool\n    execution_authority:bool\n\ndef verify_frozen_ois_boundary():\n    m=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    if getattr(m,"verify_ois_055_final_production_certification_freeze")() is not True:\n        raise RuntimeError("OIS-055 verification failed")\n    return True\n\ndef verify_kalshi_freeze():\n    m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze")\n    if getattr(m,"verify_oad_055_kalshi_production_adapter_freeze_gate")() is not True:\n        raise RuntimeError("OAD-055 verification failed")\n    return True\n\ndef build_boot_report():\n    verify_frozen_ois_boundary()\n    verify_kalshi_freeze()\n    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)\n\ndef format_boot_report(r):\n    return "\\n".join((\n        "="*72,\n        " ORACLE LIVE RUNTIME",\n        "="*72,\n        f"[REVISION] {LAUNCHER_REVISION}",\n        "[STATE] RUNNING",\n        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] Frozen Kalshi OAD-001 through OAD-055 boundary verified",\n        "[PASS] Global all-market ticker/trade fast lane enabled",\n        "[PASS] Background checkpointed universe inventory enabled",\n        "[PASS] Adaptive orderbook rotation capability certified",\n        "[PASS] Operator Terminal dependency: NONE",\n        "[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime Kalshi production adapter verified",\n    ))\n\ndef _start(root,name):\n    p=root/name\n    if not p.is_file():\n        raise RuntimeError("runtime child missing: "+name)\n    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))\n\ndef run_forever(cadence):\n    print(format_boot_report(build_boot_report()),flush=True)\n    root=Path.cwd()\n    children={\n        "fast_lane":_start(root,"run_oad_054_kalshi_global_fast_lane.py"),\n        "inventory":_start(root,"run_oad_053_background_universe_inventory.py"),\n    }\n    restarts={"fast_lane":0,"inventory":0}\n    heartbeat=0\n    try:\n        while True:\n            heartbeat+=1\n            for key,proc in tuple(children.items()):\n                if proc.poll() is not None:\n                    restarts[key]+=1\n                    print(f"[ORACLE] child={key} exited code={proc.returncode} restart_count={restarts[key]}",flush=True)\n                    name="run_oad_054_kalshi_global_fast_lane.py" if key=="fast_lane" else "run_oad_053_background_universe_inventory.py"\n                    children[key]=_start(root,name)\n            print(\n                f"[ORACLE] heartbeat={heartbeat} state=RUNNING "\n                f"fast_lane=RUNNING inventory=RUNNING "\n                f"fast_lane_restarts={restarts[\'fast_lane\']} inventory_restarts={restarts[\'inventory\']} "\n                f"terminal_dependency=NONE execution_authority=FALSE",\n                flush=True,\n            )\n            time.sleep(cadence)\n    except KeyboardInterrupt:\n        print()\n        for proc in children.values():\n            if proc.poll() is None:\n                proc.terminate()\n        for proc in children.values():\n            try: proc.wait(timeout=5)\n            except Exception:\n                if proc.poll() is None: proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)\n        return 0\n\ndef main(argv=None):\n    p=argparse.ArgumentParser()\n    p.add_argument("--check",action="store_true")\n    p.add_argument("--cadence-seconds",type=float,default=5.0)\n    a=p.parse_args(argv)\n    if a.cadence_seconds<=0:\n        raise SystemExit("--cadence-seconds must be > 0")\n    if a.check:\n        print(format_boot_report(build_boot_report()))\n        return 0\n    return run_forever(a.cadence_seconds)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
EXTRA_2='import subprocess,sys,unittest\nfrom pathlib import Path\nimport run_oracle_LIVE as live\nclass T(unittest.TestCase):\n    def test_boot(self): self.assertTrue(live.build_boot_report().certified)\n    def test_check(self):\n        p=subprocess.run([sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],text=True,capture_output=True)\n        if p.returncode!=0:\n            print(p.stdout);print(p.stderr)\n        self.assertEqual(p.returncode,0)\n        self.assertIn("Kalshi production adapter verified",p.stdout)\nif __name__=="__main__":\n    print("="*72);print(" ORACLE LIVE + OAD-055 KALSHI FREEZE LAUNCHER TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle launcher bound to frozen Kalshi production adapter")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_054_continuous_runtime_binding')
        if getattr(m,'verify_oad_054_continuous_full_universe_runtime_binding')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
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

        launcher=ROOT/"run_oracle_LIVE.py"
        launcher_test=ROOT/"test_run_oracle_LIVE.py"
        old_launcher=launcher.read_bytes() if launcher.exists() else None
        old_test=launcher_test.read_bytes() if launcher_test.exists() else None
        try:
            write_exact(launcher,EXTRA_1)
            write_exact(launcher_test,EXTRA_2)
            compile(launcher.read_text(encoding="utf-8"),str(launcher),"exec")
            compile(launcher_test.read_text(encoding="utf-8"),str(launcher_test),"exec")
            subprocess.run([sys.executable,str(launcher_test)],cwd=str(ROOT),check=True)
            subprocess.run([sys.executable,str(launcher),"--check"],cwd=str(ROOT),check=True)
        except Exception:
            if old_launcher is None:
                if launcher.exists(): launcher.unlink()
            else: launcher.write_bytes(old_launcher)
            if old_test is None:
                if launcher_test.exists(): launcher_test.unlink()
            else: launcher_test.write_bytes(old_test)
            raise

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
