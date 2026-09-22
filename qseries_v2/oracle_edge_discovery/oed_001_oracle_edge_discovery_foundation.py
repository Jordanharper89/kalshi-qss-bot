
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
