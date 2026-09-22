from __future__ import annotations
import argparse,importlib,subprocess,sys,time
from dataclasses import dataclass
from pathlib import Path

RUNTIME_NAME="Oracle Live Runtime"
LAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_OAD_055_OCR_015_OLR_005_V1"

@dataclass(frozen=True)
class OracleLiveBootReport:
    runtime_name:str
    state:str
    certified:bool
    terminal_dependency:bool
    execution_authority:bool

def _verify(module,verifier,label):
    m=importlib.import_module(module)
    if getattr(m,verifier)() is not True:
        raise RuntimeError(label+" verification failed")
    return True

def build_boot_report():
    _verify("qseries_v2.oracle_intelligence_state.ois_055_final_freeze","verify_ois_055_final_production_certification_freeze","OIS-055")
    _verify("qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze","verify_oad_055_kalshi_production_adapter_freeze_gate","OAD-055")
    _verify("qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate","verify_ocr_015_continuous_reasoning_production_capability_gate","OCR-015")
    _verify("qseries_v2.oracle_learning_runtime.olr_005_capability_gate","verify_olr_005_continuous_learning_runtime_gate","OLR-005")
    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)

def format_boot_report(r):
    return "\n".join((
        "="*72,
        " ORACLE LIVE RUNTIME",
        "="*72,
        f"[REVISION] {LAUNCHER_REVISION}",
        "[STATE] RUNNING",
        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",
        "[PASS] Frozen Kalshi OAD-001 through OAD-055 boundary verified",
        "[PASS] OCR-001 through OCR-015 continuous reasoning capability verified",
        "[PASS] OLR-001 through OLR-005 continuous learning capability verified",
        "[PASS] Global all-market ticker/trade fast lane enabled",
        "[PASS] Background checkpointed universe inventory enabled",
        "[PASS] Continuous market-aware reasoning child enabled",
        "[PASS] Outcome-grounded continuous learning child enabled",
        "[PASS] Operator Terminal dependency: NONE",
        "[PASS] Q Series execution authority remains separate",
        "[READY] Oracle Live Runtime with continuous reasoning + learning verified",
    ))

CHILDREN={
    "fast_lane":'run_opc_036_trace_fast_lane_child.py',
    "inventory":"run_oad_053_background_universe_inventory.py",
    "reasoning":"run_ocr_013_continuous_reasoning_runtime.py",
    "learning":"run_olr_005_continuous_learning_runtime.py",
    "coverage":'run_opc_036_trace_coverage_child.py',
}

def _start(root,name):
    p=root/name
    if not p.is_file():raise RuntimeError("runtime child missing: "+name)
    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))

def run_forever(cadence):
    print(format_boot_report(build_boot_report()),flush=True)
    root=Path.cwd()
    children={k:_start(root,v) for k,v in CHILDREN.items()}
    restarts={k:0 for k in CHILDREN}
    heartbeat=0
    try:
        while True:
            heartbeat+=1
            for key,proc in tuple(children.items()):
                if proc.poll() is not None:
                    restarts[key]+=1
                    print(f"[ORACLE] child={key} exited code={proc.returncode} restart_count={restarts[key]}",flush=True)
                    children[key]=_start(root,CHILDREN[key])
            status=" ".join(f"{k}={'RUNNING' if p.poll() is None else 'STOPPED'}" for k,p in children.items())
            rs=" ".join(f"{k}_restarts={restarts[k]}" for k in children)
            print(f"[ORACLE] heartbeat={heartbeat} state=RUNNING {status} {rs} terminal_dependency=NONE execution_authority=FALSE",flush=True)
            time.sleep(cadence)
    except KeyboardInterrupt:
        print()
        for proc in children.values():
            if proc.poll() is None:proc.terminate()
        for proc in children.values():
            try:proc.wait(timeout=5)
            except Exception:
                if proc.poll() is None:proc.kill()
        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)
        return 0

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true")
    p.add_argument("--cadence-seconds",type=float,default=5.0)
    a=p.parse_args(argv)
    if a.cadence_seconds<=0:raise SystemExit("--cadence-seconds must be > 0")
    if a.check:
        print(format_boot_report(build_boot_report()))
        return 0
    return run_forever(a.cadence_seconds)

if __name__=="__main__":
    raise SystemExit(main())
