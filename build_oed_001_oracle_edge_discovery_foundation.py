from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MODULE = PKG / "oed_001_oracle_edge_discovery_foundation.py"
TEST = ROOT / "test_oed_001_oracle_edge_discovery_foundation.py"

PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch()

module = r"""
SCHEMA_VERSION = "OED-001"
MISSION = (
    "Discover repeatable market inefficiencies from Oracle-observed reality "
    "without execution authority or unvalidated probability publication."
)

DISCOVERY_CLASSES = (
    "CROSS_CONTRACT_INCONSISTENCY",
    "INDEPENDENT_SOURCE_DIVERGENCE",
    "PANIC_OVERSHOOT_REVERSAL",
    "LEAD_LAG",
    "THRESHOLD_CURVE_DISTORTION",
    "TEMPORAL_INCONSISTENCY",
    "SPREAD_LIQUIDITY_DISLOCATION",
    "CROSS_VENUE_DISAGREEMENT",
    "INFORMATION_REACTION_LATENCY",
    "REGIME_SPECIFIC_BEHAVIOR",
    "EXHAUSTION_REVERSAL_SIGNATURE",
    "MARKET_FAMILY_BEHAVIORAL_FINGERPRINT",
    "MULTI_CONDITION_CROSS_DOMAIN_RELATIONSHIP",
)

VALIDATION_STATES = (
    "DISCOVERED",
    "OBSERVING",
    "REJECTED",
    "REGIME_SPECIFIC",
    "DEGRADING",
    "CERTIFIED",
)

PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

def foundation_state():
    return {
        "schema_version": SCHEMA_VERSION,
        "mission": MISSION,
        "discovery_classes": DISCOVERY_CLASSES,
        "validation_states": VALIDATION_STATES,
        "probability_enabled": PROBABILITY_ENABLED,
        "direction_enabled": DIRECTION_ENABLED,
        "publication_allowed": PUBLICATION_ALLOWED,
        "execution_authority": EXECUTION_AUTHORITY,
    }
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
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
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-001 installer complete")
