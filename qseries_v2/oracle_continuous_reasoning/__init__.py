# OCR-001 exports
from .ocr_001_foundation import (
    OCR_001_BUILD_ID,
    OCR_001_REVISION,
    ContinuousReasoningFoundation,
    verify_frozen_reasoning_boundaries,
    build_continuous_reasoning_foundation,
    verify_ocr_001_continuous_reasoning_runtime_foundation,
)

# OCR-002 exports
from .ocr_002_live_observation_read_model import (
    OCR_002_BUILD_ID,
    OCR_002_REVISION,
    LiveObservationReadResult,
    load_env,
    read_latest_canonical_observations,
    quote_sql_identifier,
    verify_ocr_002_postgresql_live_observation_read_model,
)

# OCR-003 exports
from .ocr_003_reasoning_input_batch import (
    OCR_003_BUILD_ID,
    OCR_003_REVISION,
    ReasoningObservation,
    ReasoningInputBatch,
    materialize_reasoning_observation,
    assemble_reasoning_input_batch,
    verify_ocr_003_reasoning_input_batch_assembly,
)

# OCR-004 exports
from .ocr_004_reasoning_activation_bridge import (
    OCR_004_BUILD_ID,
    OCR_004_REVISION,
    ScientificReasoningActivationEnvelope,
    build_scientific_reasoning_activation_envelope,
    verify_ocr_004_frozen_scientific_reasoning_activation_bridge,
)

# OCR-005 exports
from .ocr_005_capability_gate import (
    OCR_005_BUILD_ID,
    OCR_005_REVISION,
    OCRCapabilityCertification,
    certify_ocr_001_through_005,
    verify_ocr_005_live_reasoning_intake_activation_capability_gate,
)

# OCR-006 exports
from .ocr_006_market_identity_recovery import (
    OCR_006_BUILD_ID,
    OCR_006_REVISION,
    RecoveredMarketIdentity,
    recover_market_identity,
    recover_batch_market_identities,
    verify_ocr_006_canonical_market_identity_recovery,
)

# OCR-007 exports
from .ocr_007_umd_context_join import (
    OCR_007_BUILD_ID,
    OCR_007_REVISION,
    MarketAwareObservation,
    build_umd_context_for_recovered_identity,
    join_rows_to_umd_context,
    verify_ocr_007_umd_market_context_join,
)

# OCR-008 exports
from .ocr_008_scientific_reasoning_invocation import (
    OCR_008_BUILD_ID,
    OCR_008_REVISION,
    LiveScientificReasoningResult,
    invoke_frozen_scientific_reasoning,
    reason_over_market_aware_observations,
    verify_ocr_008_continuous_scientific_reasoning_invocation,
)

# OCR-009 exports
from .ocr_009_intelligence_state_projection import (
    OCR_009_BUILD_ID,
    OCR_009_REVISION,
    LiveIntelligenceProjection,
    project_reasoning_result_to_ois,
    project_reasoning_results,
    verify_ocr_009_intelligence_state_projection,
)

# OCR-010 exports
from .ocr_010_capability_gate import (
    OCR_010_BUILD_ID,
    OCR_010_REVISION,
    OCR010Certification,
    certify_ocr_006_through_010,
    verify_ocr_010_market_aware_continuous_reasoning_capability_gate,
)

# OCR-011 exports
from .ocr_011_reasoning_cursor_state import (
    OCR_011_BUILD_ID,
    OCR_011_REVISION,
    ReasoningCursorState,
    empty_reasoning_cursor,
    load_reasoning_cursor,
    save_reasoning_cursor,
    advance_reasoning_cursor,
    verify_ocr_011_reasoning_cursor_state,
)

# OCR-012 exports
from .ocr_012_incremental_observation_selection import (
    OCR_012_BUILD_ID,
    OCR_012_REVISION,
    IncrementalObservationSlice,
    read_new_canonical_observations,
    cursor_values_from_last_row,
    verify_ocr_012_incremental_new_observation_selection,
)

# OCR-013 exports
from .ocr_013_continuous_reasoning_loop import (
    OCR_013_BUILD_ID,
    OCR_013_REVISION,
    ContinuousReasoningCycleSummary,
    run_continuous_reasoning_cycle,
    verify_ocr_013_continuous_market_aware_reasoning_loop,
)

# OCR-014 exports
from .ocr_014_oracle_live_binding import (
    OCR_014_BUILD_ID,
    OCR_014_REVISION,
    OracleLiveReasoningBinding,
    build_oracle_live_reasoning_binding,
    verify_ocr_014_oracle_live_reasoning_child_binding,
)

# OCR-015 exports
from .ocr_015_production_gate import (
    OCR_015_BUILD_ID,
    OCR_015_REVISION,
    OCR015Certification,
    certify_ocr_011_through_015,
    verify_ocr_015_continuous_reasoning_production_capability_gate,
)
