"""
Smoke test for CORE-001 Service Registry.
Run:
    python test_core_001_service_registry.py
"""

from qseries_v2.core.service_registry import service_registry


class DemoOracleService:
    def status(self):
        return "ready"


def demo_healthcheck():
    return {
        "status": "ready",
        "message": "Demo service healthcheck passed",
    }


service_registry.register(
    service_id="oracle.demo",
    name="Demo Oracle Intelligence Service",
    category="OI",
    instance=DemoOracleService(),
    version="0.1.0",
    description="Demo service proving CORE-001 registry works.",
    healthcheck=demo_healthcheck,
    tags=["demo", "oracle", "core-001"],
    replace=True,
)

print("SERVICE LIST:")
for service in service_registry.list_services():
    print(service)

print("\nHEALTH:")
print(service_registry.health())

print("\nDIAGNOSTICS:")
print(service_registry.diagnostics())

svc = service_registry.get("oracle.demo")
print("\nDIRECT SERVICE LOOKUP:")
print(svc.status())
