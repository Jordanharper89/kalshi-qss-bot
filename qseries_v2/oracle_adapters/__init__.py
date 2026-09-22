"""Oracle Adapters - source/venue-specific read-only data acquisition subsystem."""

# OAD-001 exports
from .oad_001_foundation import (
    OAD_001_BUILD_ID,
    OAD_001_REVISION,
    OracleAdapterSubsystemPolicy,
    OracleAdapterIdentity,
    build_oracle_adapter_identity,
    build_oad_001_certification_manifest,
    verify_oad_001_oracle_adapter_subsystem_foundation,
)

# OAD-002 exports
from .oad_002_common_contract import (
    OAD_002_BUILD_ID,
    OAD_002_REVISION,
    REQUIRED_OPERATIONS,
    OracleAdapterContract,
    build_oracle_adapter_contract,
    validate_adapter_implementation,
    build_oad_002_certification_manifest,
    verify_oad_002_common_adapter_contract,
)

# OAD-003 exports
from .oad_003_canonical_event import (
    OAD_003_BUILD_ID,
    OAD_003_REVISION,
    CanonicalSourceEvent,
    build_canonical_source_event,
    build_oad_003_certification_manifest,
    verify_oad_003_canonical_source_event_envelope,
)

# OAD-004 exports
from .oad_004_lifecycle_health import (
    OAD_004_BUILD_ID,
    OAD_004_REVISION,
    ADAPTER_STATES,
    AdapterLifecycleState,
    AdapterHealthDecision,
    build_adapter_lifecycle_state,
    evaluate_adapter_health,
    build_oad_004_certification_manifest,
    verify_oad_004_adapter_lifecycle_health_contract,
)

# OAD-005 exports
from .oad_005_foundation_gate import (
    OAD_005_BUILD_ID,
    OAD_005_REVISION,
    OracleAdapterFoundationCertification,
    certify_oad_001_through_005,
    build_oad_005_certification_manifest,
    verify_oad_005_adapter_foundation_capability_gate,
)
