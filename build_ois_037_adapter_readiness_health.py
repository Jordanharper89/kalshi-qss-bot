from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_037_adapter_health.py"
TEST = ROOT / "test_ois_037_adapter_readiness_health.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_036_adapter_registry import AdapterRegistration\n\nOIS_037_BUILD_ID="OIS-037"\nOIS_037_REVISION="OIS_037_ADAPTER_READINESS_HEALTH_V1"\n\n@dataclass(frozen=True)\nclass AdapterHealth:\n    adapter_id:str\n    connected:bool\n    universe_ready:bool\n    event_stream_ready:bool\n    lag_seconds:float\n    status:str\n\ndef evaluate_adapter_health(registration,connected,universe_ready,event_stream_ready,lag_seconds,max_lag_seconds=5.0):\n    if not isinstance(registration,AdapterRegistration):\n        raise ValueError("registered adapter required")\n    lag=float(lag_seconds)\n    if lag<0:\n        raise ValueError("lag must be non-negative")\n    if not registration.enabled:\n        status="DISABLED"\n    elif not connected:\n        status="DOWN"\n    elif registration.supports_full_universe and not universe_ready:\n        status="DEGRADED"\n    elif registration.supports_event_stream and not event_stream_ready:\n        status="DEGRADED"\n    elif lag>max_lag_seconds:\n        status="LAGGING"\n    else:\n        status="READY"\n    return AdapterHealth(registration.adapter_id,bool(connected),bool(universe_ready),bool(event_stream_ready),lag,status)\n\ndef verify_ois_037_adapter_readiness_health():\n    from .ois_036_adapter_registry import register_adapter\n    a=register_adapter("kalshi_universal","kalshi")\n    return evaluate_adapter_health(a,True,True,True,1.0).status=="READY"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_036_adapter_registry import register_adapter\nfrom qseries_v2.oracle_intelligence_state.ois_037_adapter_health import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_037_adapter_readiness_health())\n\n    def test_down(self):\n        a=register_adapter("a","v")\n        self.assertEqual(evaluate_adapter_health(a,False,False,False,0).status,"DOWN")\n\n    def test_lagging(self):\n        a=register_adapter("a","v")\n        self.assertEqual(evaluate_adapter_health(a,True,True,True,6).status,"LAGGING")\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-037 CERTIFICATION TEST");print(" ADAPTER READINESS + HEALTH");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Adapter readiness/health classification certified")\n    print("[DONE] OIS-037 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_036_adapter_registry")
    if getattr(upstream, "verify_ois_036_production_adapter_registry_orchestration")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_037_adapter_health import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-037 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-037 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
