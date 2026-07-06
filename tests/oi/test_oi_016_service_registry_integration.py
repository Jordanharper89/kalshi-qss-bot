from qseries_v2.oi.service_registry_integration import (
    register_oracle_intelligence,
    get_oracle_intelligence,
)
from qseries_v2.core.service_registry import service_registry

record = register_oracle_intelligence(replace=True)
service = get_oracle_intelligence()
health = service_registry.health("oracle.intelligence")

assert record.meta.service_id == "oracle.intelligence"
assert service is not None
assert health["health"]["ok"] is True
assert health["health"]["oracle_executes"] is False

print("[PASS] OI-016 Service Registry Integration")
print(service_registry.diagnostics())
