
from qseries_v2.oracle_edge_discovery.oed_001_oracle_edge_discovery_foundation import foundation_state

s = foundation_state()
assert s["schema_version"] == "OED-001"
assert len(s["discovery_classes"]) >= 12
assert "MULTI_CONDITION_CROSS_DOMAIN_RELATIONSHIP" in s["discovery_classes"]
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
print("[DISCOVERY_CLASSES]", len(s["discovery_classes"]))
print("[PASS] OED discovery-only boundary established")
print("[PASS] multi-condition cross-domain discovery is first-class")
print("[PASS] probability/direction/publication/execution remain disabled")
print("[PASS] OED-001 Oracle Edge Discovery foundation certified")
