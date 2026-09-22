from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_049_runtime_status_read_model.py"
TEST = ROOT / "test_ois_049_oracle_runtime_status_read_model.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .ois_046_runtime_state import OracleLiveRuntimeState\nfrom .ois_048_service_health_aggregation import OracleAggregateHealth\n\nOIS_049_BUILD_ID="OIS-049"\nOIS_049_REVISION="OIS_049_ORACLE_RUNTIME_STATUS_READ_MODEL_V1"\n\n@dataclass(frozen=True)\nclass OracleRuntimeStatusReadModel:\n    runtime_state:str\n    runtime_sequence:int\n    aggregate_health:str\n    required_services:int\n    healthy_required_services:int\n    max_lag_seconds:float\n    adapter_count:int\n    read_model_generation:int\n    status_hash:str\n    read_only:bool=True\n\ndef build_runtime_status_read_model(runtime_state,aggregate_health,adapter_count,read_model_generation):\n    if not isinstance(runtime_state,OracleLiveRuntimeState) or not isinstance(aggregate_health,OracleAggregateHealth):\n        raise ValueError("certified runtime state and aggregate health required")\n    if int(adapter_count)<0 or int(read_model_generation)<0:\n        raise ValueError("non-negative runtime counters required")\n    raw={\n        "runtime_state":runtime_state.state,\n        "runtime_sequence":runtime_state.sequence,\n        "aggregate_health":aggregate_health.status,\n        "required_services":aggregate_health.required_services,\n        "healthy_required_services":aggregate_health.healthy_required_services,\n        "max_lag_seconds":aggregate_health.max_lag_seconds,\n        "adapter_count":int(adapter_count),\n        "read_model_generation":int(read_model_generation),\n    }\n    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return OracleRuntimeStatusReadModel(\n        runtime_state.state,runtime_state.sequence,aggregate_health.status,\n        aggregate_health.required_services,aggregate_health.healthy_required_services,\n        aggregate_health.max_lag_seconds,int(adapter_count),int(read_model_generation),h,True\n    )\n\ndef verify_ois_049_oracle_runtime_status_read_model():\n    from .ois_046_runtime_state import build_oracle_live_runtime_state\n    from .ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health\n    r=build_oracle_live_runtime_state("RUNNING",2,True,True)\n    h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,.1),))\n    x=build_runtime_status_read_model(r,h,0,10)\n    return x.read_only and x.runtime_state=="RUNNING" and len(x.status_hash)==64\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state\nfrom qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health\nfrom qseries_v2.oracle_intelligence_state.ois_049_runtime_status_read_model import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_049_oracle_runtime_status_read_model())\n\n    def test_read_only(self):\n        r=build_oracle_live_runtime_state("RUNNING",1,True,True)\n        h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,0),))\n        self.assertTrue(build_runtime_status_read_model(r,h,0,1).read_only)\n\n    def test_negative_counter(self):\n        r=build_oracle_live_runtime_state("RUNNING",1,True,True)\n        h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,0),))\n        with self.assertRaises(ValueError):\n            build_runtime_status_read_model(r,h,-1,1)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-049 CERTIFICATION TEST");print(" ORACLE RUNTIME STATUS READ MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Read-only Oracle runtime status model certified")\n    print("[DONE] OIS-049 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation")
    if getattr(upstream, "verify_ois_048_runtime_service_registry_health_aggregation")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_049_runtime_status_read_model import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-049 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-049 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
