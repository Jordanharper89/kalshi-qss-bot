from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_019_coverage_recovery_health_supervision.py"
TEST=ROOT/"test_opc_019_coverage_recovery_health_supervision.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport socket, ssl, urllib.error\n\n@dataclass(frozen=True)\nclass CoverageHealth:\n    health:str\n    restart_recommended:bool\n    reason:str\n    consecutive_failures:int\n    execution_authority:bool=False\n\ndef is_transient_coverage_exception(exc):\n    return isinstance(\n        exc,\n        (\n            TimeoutError,\n            ConnectionError,\n            socket.timeout,\n            ssl.SSLError,\n            urllib.error.URLError,\n        ),\n    )\n\ndef evaluate_coverage_health(state,max_consecutive_failures=3):\n    failures=int(getattr(state,"consecutive_failures",0))\n    status=str(getattr(state,"last_cycle_status","NEVER_RUN"))\n    if failures>=int(max_consecutive_failures):\n        return CoverageHealth("DEGRADED",True,"CONSECUTIVE_FAILURE_THRESHOLD",failures,False)\n    if status in ("SUCCESS","NEVER_RUN"):\n        return CoverageHealth("HEALTHY",False,status,failures,False)\n    return CoverageHealth("OBSERVE",False,status,failures,False)\n\ndef bounded_retry_delays(attempts=3,base_seconds=1.0,max_seconds=30.0):\n    attempts=int(attempts)\n    return tuple(min(float(max_seconds),float(base_seconds)*(2**i)) for i in range(attempts))\n\ndef verify_opc_019_coverage_recovery_health_supervision():\n    class S:\n        consecutive_failures=3\n        last_cycle_status="FAILED"\n    h=evaluate_coverage_health(S(),3)\n    return h.health=="DEGRADED" and h.restart_recommended and is_transient_coverage_exception(TimeoutError())\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_019_coverage_recovery_health_supervision import verify_opc_019_coverage_recovery_health_supervision\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_019_coverage_recovery_health_supervision())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-019 CERTIFICATION TEST")\n    print(" COVERAGE RECOVERY HEALTH SUPERVISION")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-019 certified")\n    print("[DONE] OPC-019 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-019 INSTALLER")
    print(" COVERAGE RECOVERY HEALTH SUPERVISION")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_018_bounded_continuous_coverage_runner")
    if up.verify_opc_018_bounded_continuous_coverage_runner() is not True:
        raise RuntimeError("Certified OPC-018 verification failed")
    print("[PASS] Certified OPC-018 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export_line="from .opc_019_coverage_recovery_health_supervision import *"
        if export_line not in current:
            write_exact(INIT,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )
    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)
        print("[ROLLBACK] OPC-019 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-019 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
