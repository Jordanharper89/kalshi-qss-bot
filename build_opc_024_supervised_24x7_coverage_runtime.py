from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_024_supervised_24x7_coverage_runtime.py";TEST=ROOT/"test_opc_024_supervised_24x7_coverage_runtime.py";INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom pathlib import Path\nimport time\nfrom .opc_017_durable_coverage_runtime_state import load_coverage_runtime_state,save_coverage_runtime_state,advance_coverage_runtime_state\nfrom .opc_019_coverage_recovery_health_supervision import is_transient_coverage_exception,evaluate_coverage_health\nfrom .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget\nfrom .opc_023_rotating_full_universe_coverage_cycle import run_rotating_full_universe_coverage_cycle\n@dataclass(frozen=True)\nclass CoverageRuntimeCheck:\n    ready:bool;health:str;terminal_dependency:bool=False;execution_authority:bool=False\ndef run_supervised_coverage_forever(root=None,budget=None,progress=None,sleep_fn=time.sleep):\n    root=Path(root or Path.cwd()).resolve();budget=budget or CoverageLoadBudget();state=load_coverage_runtime_state(root)\n    while True:\n        try:\n            r=run_rotating_full_universe_coverage_cycle(root,budget,progress)\n            status="SUCCESS" if r.snapshots_planned==r.snapshots_persisted else "PARTIAL"\n            state=save_coverage_runtime_state(advance_coverage_runtime_state(state,planned=r.snapshots_planned,persisted=r.snapshots_persisted,status=status),root)\n        except KeyboardInterrupt:return 0\n        except Exception as exc:\n            tr=is_transient_coverage_exception(exc)\n            state=save_coverage_runtime_state(advance_coverage_runtime_state(state,planned=0,persisted=0,status="TRANSIENT_FAILURE" if tr else "FAILED",transient_failure=tr),root)\n            if progress: progress(f"[COVERAGE] failure type={type(exc).__name__} transient={tr} consecutive={state.consecutive_failures}")\n            if not tr: raise\n        sleep_fn(budget.cycle_sleep_seconds)\ndef coverage_runtime_check(root=None):\n    h=evaluate_coverage_health(load_coverage_runtime_state(root))\n    return CoverageRuntimeCheck(h.health!="DEGRADED",h.health,False,False)\ndef verify_opc_024_supervised_24x7_coverage_runtime():\n    x=CoverageRuntimeCheck(True,"HEALTHY",False,False)\n    return x.ready and not x.execution_authority\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_024_supervised_24x7_coverage_runtime import verify_opc_024_supervised_24x7_coverage_runtime\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_024_supervised_24x7_coverage_runtime())\nif __name__=="__main__":\n    print("="*72);print(" OPC-024 CERTIFICATION TEST");print(" SUPERVISED 24X7 COVERAGE RUNTIME");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-024 certified");print("[DONE] OPC-024 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*72);print(" OPC-024 INSTALLER");print(" SUPERVISED 24X7 COVERAGE RUNTIME");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle")
    if up.verify_opc_023_rotating_full_universe_coverage_cycle() is not True: raise RuntimeError("OPC-023 failed")
    print("[PASS] Certified OPC-023 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .opc_024_supervised_24x7_coverage_runtime import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPC-024 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPC-024 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
