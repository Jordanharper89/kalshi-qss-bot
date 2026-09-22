from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_048_service_health_aggregation.py"
TEST = ROOT / "test_ois_048_runtime_service_registry_health_aggregation.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_048_BUILD_ID="OIS-048"\nOIS_048_REVISION="OIS_048_RUNTIME_SERVICE_REGISTRY_HEALTH_AGGREGATION_V1"\n\n@dataclass(frozen=True)\nclass RuntimeServiceHealth:\n    service_id:str\n    required:bool\n    healthy:bool\n    lag_seconds:float\n    status:str\n\n@dataclass(frozen=True)\nclass OracleAggregateHealth:\n    required_services:int\n    healthy_required_services:int\n    degraded_services:tuple[str,...]\n    max_lag_seconds:float\n    status:str\n\ndef build_runtime_service_health(service_id,required,healthy,lag_seconds,status=None):\n    lag=float(lag_seconds)\n    if not service_id or lag<0:\n        raise ValueError("valid service health required")\n    st=status or ("HEALTHY" if healthy else "DEGRADED")\n    return RuntimeServiceHealth(service_id,bool(required),bool(healthy),lag,st)\n\ndef aggregate_runtime_health(services,max_allowed_lag_seconds=30.0):\n    rows=tuple(sorted(services,key=lambda x:x.service_id))\n    if not rows:\n        raise ValueError("runtime services required")\n    required=tuple(x for x in rows if x.required)\n    healthy=sum(1 for x in required if x.healthy and x.lag_seconds<=max_allowed_lag_seconds)\n    degraded=tuple(x.service_id for x in rows if (not x.healthy or x.lag_seconds>max_allowed_lag_seconds))\n    max_lag=max(x.lag_seconds for x in rows)\n    status="HEALTHY" if healthy==len(required) else "DEGRADED"\n    return OracleAggregateHealth(len(required),healthy,degraded,max_lag,status)\n\ndef verify_ois_048_runtime_service_registry_health_aggregation():\n    services=(\n        build_runtime_service_health("live_shadow",True,True,.1),\n        build_runtime_service_health("postgresql",True,True,.1),\n        build_runtime_service_health("oi",True,True,.2),\n        build_runtime_service_health("umd",True,True,.2),\n        build_runtime_service_health("oml",True,True,.2),\n        build_runtime_service_health("ocl",True,True,.3),\n        build_runtime_service_health("osr",True,True,.3),\n        build_runtime_service_health("ois",True,True,.1),\n    )\n    x=aggregate_runtime_health(services)\n    return x.status=="HEALTHY" and x.required_services==8 and not x.degraded_services\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_048_runtime_service_registry_health_aggregation())\n\n    def test_degraded_required(self):\n        x=aggregate_runtime_health((\n            build_runtime_service_health("a",True,True,0),\n            build_runtime_service_health("b",True,False,0),\n        ))\n        self.assertEqual(x.status,"DEGRADED")\n\n    def test_lag_degrades(self):\n        x=aggregate_runtime_health((build_runtime_service_health("a",True,True,31),))\n        self.assertEqual(x.status,"DEGRADED")\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-048 CERTIFICATION TEST");print(" RUNTIME SERVICE REGISTRY + HEALTH AGGREGATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle runtime service health aggregation certified")\n    print("[DONE] OIS-048 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_047_runtime_activation")
    if getattr(upstream, "verify_ois_047_oracle_live_runtime_activation_controller")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_048_service_health_aggregation import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-048 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-048 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
