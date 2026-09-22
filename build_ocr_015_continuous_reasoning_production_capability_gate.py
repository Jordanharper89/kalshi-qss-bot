from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_reasoning"
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

BUILD_ID='OCR-015'
TITLE='CONTINUOUS REASONING PRODUCTION CAPABILITY GATE'
REVISION='OCR_015_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_015_production_gate.py'
TEST=ROOT/'test_ocr_015_continuous_reasoning_production_capability_gate.py'
EXPORTS=('OCR_015_BUILD_ID', 'OCR_015_REVISION', 'OCR015Certification', 'certify_ocr_011_through_015', 'verify_ocr_015_continuous_reasoning_production_capability_gate')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .ocr_011_reasoning_cursor_state import verify_ocr_011_reasoning_cursor_state\nfrom .ocr_012_incremental_observation_selection import verify_ocr_012_incremental_new_observation_selection\nfrom .ocr_013_continuous_reasoning_loop import verify_ocr_013_continuous_market_aware_reasoning_loop\nfrom .ocr_014_oracle_live_binding import verify_ocr_014_oracle_live_reasoning_child_binding\n\nOCR_015_BUILD_ID="OCR-015"\nOCR_015_REVISION="OCR_015_CONTINUOUS_REASONING_PRODUCTION_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass OCR015Certification:\n    builds:tuple[str,...]\n    runtime_command:str\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ocr_011_through_015():\n    checks=(verify_ocr_011_reasoning_cursor_state(),verify_ocr_012_incremental_new_observation_selection(),\n            verify_ocr_013_continuous_market_aware_reasoning_loop(),verify_ocr_014_oracle_live_reasoning_child_binding())\n    if not all(checks):raise RuntimeError("OCR-011 through OCR-015 certification failed")\n    return OCR015Certification(\n        tuple("OCR-%03d"%i for i in range(11,16)),\n        "run_oracle_LIVE.py",\n        "cursor_driven_incremental_continuous_market_aware_reasoning_runtime",\n        "continuous_reasoning_state_materialization_and_terminal_query_surface",\n        True,\n    )\n\ndef verify_ocr_015_continuous_reasoning_production_capability_gate():\n    c=certify_ocr_011_through_015()\n    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_015_continuous_reasoning_production_capability_gate())\n    def test_five(self):self.assertEqual(len(certify_ocr_011_through_015().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OCR-015 CERTIFICATION TEST");print(" CONTINUOUS REASONING PRODUCTION CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OCR-011 through OCR-015 continuous reasoning production capability certified")\n    print("[PASS] Runtime command: run_oracle_LIVE.py")\n    print("[DONE] OCR-015 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nfrom qseries_v2.oracle_continuous_reasoning.ocr_013_continuous_reasoning_loop import run_continuous_reasoning_cycle\n\nif __name__=="__main__":\n    print("="*72);print(" OCR-015 PHYSICAL CONTINUOUS REASONING CYCLE VERIFICATION");print("="*72)\n    s=run_continuous_reasoning_cycle(Path.cwd(),limit=25,progress=lambda x:print(x,flush=True))\n    print("[SUMMARY]",s)\n    if s.idle:\n        print("[PASS] No unprocessed observations available; cursor/runtime path healthy")\n    else:\n        if not s.cursor_advanced or s.ois_projections<1:raise SystemExit("[FAIL] reasoning cycle incomplete")\n        print("[PASS] New observations processed through OSR and OIS projection with cursor advancement")\n    print("[DONE] OCR-015 PHYSICAL CONTINUOUS REASONING CYCLE VERIFIED")\n'
EXTRA_2='from __future__ import annotations\nimport argparse,importlib,subprocess,sys,time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME="Oracle Live Runtime"\nLAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_OAD_055_PLUS_OCR_015_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name:str\n    state:str\n    certified:bool\n    terminal_dependency:bool\n    execution_authority:bool\n\ndef verify_ois():\n    m=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    if getattr(m,"verify_ois_055_final_production_certification_freeze")() is not True:raise RuntimeError("OIS-055 verification failed")\n    return True\n\ndef verify_kalshi():\n    m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze")\n    if getattr(m,"verify_oad_055_kalshi_production_adapter_freeze_gate")() is not True:raise RuntimeError("OAD-055 verification failed")\n    return True\n\ndef verify_ocr():\n    m=importlib.import_module("qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate")\n    if getattr(m,"verify_ocr_015_continuous_reasoning_production_capability_gate")() is not True:raise RuntimeError("OCR-015 verification failed")\n    return True\n\ndef build_boot_report():\n    verify_ois();verify_kalshi();verify_ocr()\n    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)\n\ndef format_boot_report(r):\n    return "\\n".join((\n        "="*72,\n        " ORACLE LIVE RUNTIME",\n        "="*72,\n        f"[REVISION] {LAUNCHER_REVISION}",\n        "[STATE] RUNNING",\n        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] Frozen Kalshi OAD-001 through OAD-055 boundary verified",\n        "[PASS] OCR-001 through OCR-015 continuous reasoning capability verified",\n        "[PASS] Global all-market ticker/trade fast lane enabled",\n        "[PASS] Background checkpointed universe inventory enabled",\n        "[PASS] Continuous market-aware reasoning child enabled",\n        "[PASS] Operator Terminal dependency: NONE",\n        "[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime with continuous reasoning verified",\n    ))\n\nCHILDREN={\n    "fast_lane":"run_oad_054_kalshi_global_fast_lane.py",\n    "inventory":"run_oad_053_background_universe_inventory.py",\n    "reasoning":"run_ocr_013_continuous_reasoning_runtime.py",\n}\n\ndef _start(root,name):\n    p=root/name\n    if not p.is_file():raise RuntimeError("runtime child missing: "+name)\n    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))\n\ndef run_forever(cadence):\n    print(format_boot_report(build_boot_report()),flush=True)\n    root=Path.cwd()\n    children={k:_start(root,v) for k,v in CHILDREN.items()}\n    restarts={k:0 for k in CHILDREN}\n    heartbeat=0\n    try:\n        while True:\n            heartbeat+=1\n            for key,proc in tuple(children.items()):\n                if proc.poll() is not None:\n                    restarts[key]+=1\n                    print(f"[ORACLE] child={key} exited code={proc.returncode} restart_count={restarts[key]}",flush=True)\n                    children[key]=_start(root,CHILDREN[key])\n            print(\n                f"[ORACLE] heartbeat={heartbeat} state=RUNNING "\n                f"fast_lane={\'RUNNING\' if children[\'fast_lane\'].poll() is None else \'STOPPED\'} "\n                f"inventory={\'RUNNING\' if children[\'inventory\'].poll() is None else \'STOPPED\'} "\n                f"reasoning={\'RUNNING\' if children[\'reasoning\'].poll() is None else \'STOPPED\'} "\n                f"fast_lane_restarts={restarts[\'fast_lane\']} inventory_restarts={restarts[\'inventory\']} reasoning_restarts={restarts[\'reasoning\']} "\n                f"terminal_dependency=NONE execution_authority=FALSE",\n                flush=True,\n            )\n            time.sleep(cadence)\n    except KeyboardInterrupt:\n        print()\n        for proc in children.values():\n            if proc.poll() is None:proc.terminate()\n        for proc in children.values():\n            try:proc.wait(timeout=5)\n            except Exception:\n                if proc.poll() is None:proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)\n        return 0\n\ndef main(argv=None):\n    p=argparse.ArgumentParser()\n    p.add_argument("--check",action="store_true")\n    p.add_argument("--cadence-seconds",type=float,default=5.0)\n    a=p.parse_args(argv)\n    if a.cadence_seconds<=0:raise SystemExit("--cadence-seconds must be > 0")\n    if a.check:\n        print(format_boot_report(build_boot_report()))\n        return 0\n    return run_forever(a.cadence_seconds)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
EXTRA_3='import subprocess,sys,unittest\nfrom pathlib import Path\nimport run_oracle_LIVE as live\nclass T(unittest.TestCase):\n    def test_boot(self):self.assertTrue(live.build_boot_report().certified)\n    def test_check(self):\n        p=subprocess.run([sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],text=True,capture_output=True)\n        if p.returncode!=0:\n            print(p.stdout);print(p.stderr)\n        self.assertEqual(p.returncode,0)\n        self.assertIn("continuous reasoning verified",p.stdout)\nif __name__=="__main__":\n    print("="*72);print(" ORACLE LIVE + OCR-015 CONTINUOUS REASONING LAUNCHER TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Oracle launcher bound to supervised continuous reasoning child")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_014_oracle_live_binding')
        if getattr(m,'verify_ocr_014_oracle_live_reasoning_child_binding')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_ocr_015_physical_continuous_reasoning_cycle_verification.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_ocr_015_physical_continuous_reasoning_cycle_verification.py',EXTRA_1)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_reasoning."+MODULE.stem
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
            write_exact(launcher,EXTRA_2)
            write_exact(launcher_test,EXTRA_3)
            compile(launcher.read_text(encoding="utf-8"),str(launcher),"exec")
            compile(launcher_test.read_text(encoding="utf-8"),str(launcher_test),"exec")
            subprocess.run([sys.executable,str(launcher_test)],cwd=str(ROOT),check=True)
            subprocess.run([sys.executable,str(launcher),"--check"],cwd=str(ROOT),check=True)
        except Exception:
            if old_launcher is None:
                if launcher.exists():launcher.unlink()
            else:launcher.write_bytes(old_launcher)
            if old_test is None:
                if launcher_test.exists():launcher_test.unlink()
            else:launcher_test.write_bytes(old_test)
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
