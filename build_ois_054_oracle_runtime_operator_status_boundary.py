from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_054_operator_status_boundary.py"
TEST = ROOT / "test_ois_054_oracle_runtime_operator_status_boundary.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_049_runtime_status_read_model import OracleRuntimeStatusReadModel\n\nOIS_054_BUILD_ID="OIS-054"\nOIS_054_REVISION="OIS_054_ORACLE_RUNTIME_OPERATOR_STATUS_BOUNDARY_V1"\n\n@dataclass(frozen=True)\nclass OperatorRuntimeStatus:\n    runtime_state:str\n    health:str\n    services_ready:str\n    max_lag_seconds:float\n    adapter_count:int\n    read_model_generation:int\n    read_only:bool=True\n\ndef project_operator_runtime_status(status):\n    if not isinstance(status,OracleRuntimeStatusReadModel):\n        raise ValueError("certified runtime status read model required")\n    services=f"{status.healthy_required_services}/{status.required_services}"\n    return OperatorRuntimeStatus(\n        status.runtime_state,\n        status.aggregate_health,\n        services,\n        status.max_lag_seconds,\n        status.adapter_count,\n        status.read_model_generation,\n        True,\n    )\n\ndef verify_ois_054_oracle_runtime_operator_status_boundary():\n    from .ois_046_runtime_state import build_oracle_live_runtime_state\n    from .ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health\n    from .ois_049_runtime_status_read_model import build_runtime_status_read_model\n    r=build_oracle_live_runtime_state("RUNNING",1,True,True)\n    h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,.1),))\n    s=build_runtime_status_read_model(r,h,0,5)\n    p=project_operator_runtime_status(s)\n    return p.read_only and p.runtime_state=="RUNNING" and p.services_ready=="1/1"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_054_operator_status_boundary import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_054_oracle_runtime_operator_status_boundary())\n\n    def test_read_only(self):\n        from qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state\n        from qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health\n        from qseries_v2.oracle_intelligence_state.ois_049_runtime_status_read_model import build_runtime_status_read_model\n        r=build_oracle_live_runtime_state("RUNNING",1,True,True)\n        h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,0),))\n        self.assertTrue(project_operator_runtime_status(build_runtime_status_read_model(r,h,0,1)).read_only)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-054 CERTIFICATION TEST");print(" ORACLE RUNTIME OPERATOR STATUS BOUNDARY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Read-only Operator Terminal/API runtime status boundary certified")\n    print("[DONE] OIS-054 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_053_runtime_supervision")
    if getattr(upstream, "verify_ois_053_24x7_runtime_supervision_automatic_recovery")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_054_operator_status_boundary import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-054 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-054 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
