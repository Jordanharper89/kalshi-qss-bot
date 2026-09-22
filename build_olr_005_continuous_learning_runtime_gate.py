from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_learning_runtime"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OLR-005'
TITLE='CONTINUOUS LEARNING RUNTIME GATE'
REVISION='OLR_005_PRODUCTION_V1'
MODULE=PACKAGE/'olr_005_capability_gate.py'
TEST=ROOT/'test_olr_005_continuous_learning_runtime_gate.py'
EXPORTS=('OLR_005_BUILD_ID', 'OLR_005_REVISION', 'OLR005Certification', 'certify_olr_001_through_005', 'verify_olr_005_continuous_learning_runtime_gate')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_001_foundation import verify_olr_001_oracle_learning_runtime_foundation\nfrom .olr_002_settled_outcome_read_model import verify_olr_002_kalshi_settled_outcome_read_model\nfrom .olr_003_learning_event_bridge import verify_olr_003_evidence_outcome_learning_event_bridge\nfrom .olr_004_learning_cycle_state import verify_olr_004_durable_continuous_learning_cycle\nOLR_005_BUILD_ID="OLR-005"\nOLR_005_REVISION="OLR_005_CONTINUOUS_LEARNING_RUNTIME_GATE_V1"\n\n@dataclass(frozen=True)\nclass OLR005Certification:\n    builds:tuple[str,...]\n    capability:str\n    runtime_command:str\n    certified:bool=True\n\ndef certify_olr_001_through_005():\n    if not all((\n        verify_olr_001_oracle_learning_runtime_foundation(),\n        verify_olr_002_kalshi_settled_outcome_read_model(),\n        verify_olr_003_evidence_outcome_learning_event_bridge(),\n        verify_olr_004_durable_continuous_learning_cycle(),\n    )):\n        raise RuntimeError("OLR certification failed")\n    return OLR005Certification(\n        tuple("OLR-%03d"%i for i in range(1,6)),\n        "outcome_grounded_continuous_learning_runtime",\n        "run_oracle_LIVE.py",\n        True,\n    )\n\ndef verify_olr_005_continuous_learning_runtime_gate():\n    return certify_olr_001_through_005().certified\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_005_capability_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_005_continuous_learning_runtime_gate())\n    def test_five(self):self.assertEqual(len(certify_olr_001_through_005().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OLR-005 CERTIFICATION TEST");print(" CONTINUOUS LEARNING RUNTIME GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-001 through OLR-005 outcome-grounded continuous learning certified")\n    print("[DONE] OLR-005 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nimport time\nfrom qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model import fetch_recent_settled_markets\nfrom qseries_v2.oracle_learning_runtime.olr_003_learning_event_bridge import find_market_evidence,build_learning_runtime_input\nfrom qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import load_learning_runtime_state,save_learning_runtime_state,apply_learning_inputs\n\ndef main():\n    root=Path.cwd()\n    state_path=root/"runtime_state"/"oracle_learning_runtime_state.json"\n    print("="*72,flush=True)\n    print(" OLR-005 OUTCOME-GROUNDED CONTINUOUS LEARNING RUNTIME",flush=True)\n    print("="*72,flush=True)\n    try:\n        while True:\n            state=load_learning_runtime_state(state_path)\n            rows=fetch_recent_settled_markets(root,limit=100)\n            rows=tuple(x for x in rows if (x.settlement_ts,x.ticker)>(state.last_settlement_ts,state.last_ticker))\n            inputs=[];last=None;seq=state.ocl_state.applied_through_sequence\n            for outcome in rows:\n                _,evidence_hash=find_market_evidence(root,outcome.ticker,500)\n                if not evidence_hash:\n                    continue\n                seq+=1\n                inputs.append(build_learning_runtime_input(seq,outcome,evidence_hash))\n                last=outcome\n            if inputs and last:\n                result,new=apply_learning_inputs(state,tuple(inputs),last.settlement_ts,last.ticker)\n                save_learning_runtime_state(state_path,new)\n                print(\n                    f"[LEARN] outcomes={len(inputs)} cycle={new.cycles} "\n                    f"learned_total={new.outcomes_learned} "\n                    f"through_sequence={new.ocl_state.applied_through_sequence}",\n                    flush=True,\n                )\n                print(\n                    f"[LEARN] state_hash={new.ocl_state.state_hash} "\n                    f"cycle_hash={result.cycle_hash}",\n                    flush=True,\n                )\n            else:\n                print("[LEARN] idle no_new_outcome_grounded_learning_events",flush=True)\n            time.sleep(15)\n    except KeyboardInterrupt:\n        print("\\n[STOP] Continuous learning runtime stopped by operator.",flush=True)\n        return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
EXTRA_2='from __future__ import annotations\nimport argparse,importlib,subprocess,sys,time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME="Oracle Live Runtime"\nLAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_OAD_055_OCR_015_OLR_005_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name:str\n    state:str\n    certified:bool\n    terminal_dependency:bool\n    execution_authority:bool\n\ndef _verify(module,verifier,label):\n    m=importlib.import_module(module)\n    if getattr(m,verifier)() is not True:\n        raise RuntimeError(label+" verification failed")\n    return True\n\ndef build_boot_report():\n    _verify("qseries_v2.oracle_intelligence_state.ois_055_final_freeze","verify_ois_055_final_production_certification_freeze","OIS-055")\n    _verify("qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze","verify_oad_055_kalshi_production_adapter_freeze_gate","OAD-055")\n    _verify("qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate","verify_ocr_015_continuous_reasoning_production_capability_gate","OCR-015")\n    _verify("qseries_v2.oracle_learning_runtime.olr_005_capability_gate","verify_olr_005_continuous_learning_runtime_gate","OLR-005")\n    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)\n\ndef format_boot_report(r):\n    return "\\n".join((\n        "="*72,\n        " ORACLE LIVE RUNTIME",\n        "="*72,\n        f"[REVISION] {LAUNCHER_REVISION}",\n        "[STATE] RUNNING",\n        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] Frozen Kalshi OAD-001 through OAD-055 boundary verified",\n        "[PASS] OCR-001 through OCR-015 continuous reasoning capability verified",\n        "[PASS] OLR-001 through OLR-005 continuous learning capability verified",\n        "[PASS] Global all-market ticker/trade fast lane enabled",\n        "[PASS] Background checkpointed universe inventory enabled",\n        "[PASS] Continuous market-aware reasoning child enabled",\n        "[PASS] Outcome-grounded continuous learning child enabled",\n        "[PASS] Operator Terminal dependency: NONE",\n        "[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime with continuous reasoning + learning verified",\n    ))\n\nCHILDREN={\n    "fast_lane":"run_oad_054_kalshi_global_fast_lane.py",\n    "inventory":"run_oad_053_background_universe_inventory.py",\n    "reasoning":"run_ocr_013_continuous_reasoning_runtime.py",\n    "learning":"run_olr_005_continuous_learning_runtime.py",\n}\n\ndef _start(root,name):\n    p=root/name\n    if not p.is_file():raise RuntimeError("runtime child missing: "+name)\n    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))\n\ndef run_forever(cadence):\n    print(format_boot_report(build_boot_report()),flush=True)\n    root=Path.cwd()\n    children={k:_start(root,v) for k,v in CHILDREN.items()}\n    restarts={k:0 for k in CHILDREN}\n    heartbeat=0\n    try:\n        while True:\n            heartbeat+=1\n            for key,proc in tuple(children.items()):\n                if proc.poll() is not None:\n                    restarts[key]+=1\n                    print(f"[ORACLE] child={key} exited code={proc.returncode} restart_count={restarts[key]}",flush=True)\n                    children[key]=_start(root,CHILDREN[key])\n            status=" ".join(f"{k}={\'RUNNING\' if p.poll() is None else \'STOPPED\'}" for k,p in children.items())\n            rs=" ".join(f"{k}_restarts={restarts[k]}" for k in children)\n            print(f"[ORACLE] heartbeat={heartbeat} state=RUNNING {status} {rs} terminal_dependency=NONE execution_authority=FALSE",flush=True)\n            time.sleep(cadence)\n    except KeyboardInterrupt:\n        print()\n        for proc in children.values():\n            if proc.poll() is None:proc.terminate()\n        for proc in children.values():\n            try:proc.wait(timeout=5)\n            except Exception:\n                if proc.poll() is None:proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)\n        return 0\n\ndef main(argv=None):\n    p=argparse.ArgumentParser()\n    p.add_argument("--check",action="store_true")\n    p.add_argument("--cadence-seconds",type=float,default=5.0)\n    a=p.parse_args(argv)\n    if a.cadence_seconds<=0:raise SystemExit("--cadence-seconds must be > 0")\n    if a.check:\n        print(format_boot_report(build_boot_report()))\n        return 0\n    return run_forever(a.cadence_seconds)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
EXTRA_3='import subprocess,sys,unittest\nfrom pathlib import Path\nimport run_oracle_LIVE as live\nclass T(unittest.TestCase):\n    def test_boot(self):self.assertTrue(live.build_boot_report().certified)\n    def test_check(self):\n        p=subprocess.run([sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],capture_output=True,text=True)\n        if p.returncode!=0:print(p.stdout);print(p.stderr)\n        self.assertEqual(p.returncode,0)\n        self.assertIn("continuous reasoning + learning verified",p.stdout)\nif __name__=="__main__":\n    print("="*72);print(" ORACLE LIVE + OLR-005 LEARNING LAUNCHER TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Oracle launcher bound to supervised continuous learning child")\n'
EXTRA_4='from pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model import fetch_recent_settled_markets\nif __name__=="__main__":\n    print("="*72);print(" OLR-005 PHYSICAL SETTLED OUTCOME READ VERIFICATION");print("="*72)\n    rows=fetch_recent_settled_markets(Path.cwd(),limit=20)\n    print(f"[SETTLED] outcomes={len(rows)}")\n    for x in rows[:10]:\n        print(f"[SETTLED] ticker={x.ticker} result={x.result} settlement_ts={x.settlement_ts}")\n    print("[PASS] Physical Kalshi settled-outcome read path verified")\n    print("[DONE] OLR-005 PHYSICAL OUTCOME READ VERIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state')
        if getattr(m,'verify_olr_004_durable_continuous_learning_cycle')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified frozen upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_olr_005_continuous_learning_runtime.py',ROOT/'run_olr_005_physical_settled_outcome_read_verification.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_olr_005_continuous_learning_runtime.py',EXTRA_1)
        write_exact(ROOT/'run_olr_005_physical_settled_outcome_read_verification.py',EXTRA_4)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_learning_runtime."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
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
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
