"""Kalshi read-only Oracle adapter implementation."""

# OAD-006 exports
from .oad_006_kalshi_foundation import (
    OAD_006_BUILD_ID,
    OAD_006_REVISION,
    KalshiAdapterFoundation,
    build_kalshi_adapter_foundation,
    build_oad_006_certification_manifest,
    verify_oad_006_kalshi_adapter_foundation,
)

# OAD-007 exports
from .oad_007_transport_auth import (
    OAD_007_BUILD_ID,
    OAD_007_REVISION,
    KalshiTransportAuthBoundary,
    signing_message,
    build_kalshi_transport_auth_boundary,
    build_oad_007_certification_manifest,
    verify_oad_007_kalshi_transport_auth_boundary,
)

# OAD-008 exports
from .oad_008_full_universe_discovery import (
    OAD_008_BUILD_ID,
    OAD_008_REVISION,
    KALSHI_MARKET_FILTERS,
    KalshiMarketRecord,
    KalshiUniverseSnapshot,
    build_markets_page_request,
    normalize_market,
    build_full_universe_snapshot,
    build_oad_008_certification_manifest,
    verify_oad_008_kalshi_full_universe_discovery,
)

# OAD-009 exports
from .oad_009_universe_reconciliation import (
    OAD_009_BUILD_ID,
    OAD_009_REVISION,
    KalshiMarketLifecycleClass,
    KalshiUniverseReconciliation,
    classify_market,
    reconcile_universe,
    build_oad_009_certification_manifest,
    verify_oad_009_kalshi_universe_reconciliation_lifecycle,
)

# OAD-010 exports
from .oad_010_kalshi_discovery_gate import (
    OAD_010_BUILD_ID,
    OAD_010_REVISION,
    KalshiDiscoveryCapabilityCertification,
    certify_oad_006_through_010,
    build_oad_010_certification_manifest,
    verify_oad_010_kalshi_full_universe_discovery_capability_gate,
)

# OAD-011 exports
from .oad_011_websocket_foundation import (
    OAD_011_BUILD_ID,
    OAD_011_REVISION,
    PUBLIC_MARKET_DATA_CHANNELS,
    KalshiWebSocketMarketDataFoundation,
    build_websocket_market_data_foundation,
    build_subscribe_command,
    build_oad_011_certification_manifest,
    verify_oad_011_kalshi_websocket_market_data_foundation,
)

# OAD-012 exports
from .oad_012_subscription_partitioning import (
    OAD_012_BUILD_ID,
    OAD_012_REVISION,
    SubscriptionPartition,
    SubscriptionCoveragePlan,
    partition_subscriptions,
    build_partition_subscribe_commands,
    build_oad_012_certification_manifest,
    verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage,
)

# OAD-013 exports
from .oad_013_market_data_normalization import (
    OAD_013_BUILD_ID,
    OAD_013_REVISION,
    NormalizedKalshiMarketData,
    normalize_kalshi_market_data,
    build_oad_013_certification_manifest,
    verify_oad_013_kalshi_orderbook_trade_ticker_normalization,
)

# OAD-014 exports
from .oad_014_sequence_integrity import (
    OAD_014_BUILD_ID,
    OAD_014_REVISION,
    SequenceIntegrityDecision,
    evaluate_sequence_integrity,
    build_orderbook_resync_command,
    build_oad_014_certification_manifest,
    verify_oad_014_kalshi_sequence_integrity_gap_detection_resync,
)

# OAD-015 exports
from .oad_015_streaming_gate import (
    OAD_015_BUILD_ID,
    OAD_015_REVISION,
    KalshiStreamingCapabilityCertification,
    certify_oad_011_through_015,
    build_oad_015_certification_manifest,
    verify_oad_015_kalshi_low_latency_streaming_capability_gate,
)

# OAD-016 exports
from .oad_016_reconnect_recovery import (
    OAD_016_BUILD_ID,
    OAD_016_REVISION,
    ReconnectRecoveryPlan,
    build_reconnect_recovery_plan,
    build_recovery_subscribe_commands,
    recovery_ready,
    build_oad_016_certification_manifest,
    verify_oad_016_kalshi_reconnect_resubscribe_recovery,
)

# OAD-017 exports
from .oad_017_keepalive_liveness import (
    OAD_017_BUILD_ID,
    OAD_017_REVISION,
    KeepaliveState,
    evaluate_keepalive,
    should_reconnect_keepalive,
    build_oad_017_certification_manifest,
    verify_oad_017_kalshi_keepalive_liveness_supervision,
)

# OAD-018 exports
from .oad_018_latency_telemetry import (
    OAD_018_BUILD_ID,
    OAD_018_REVISION,
    KalshiLatencySample,
    KalshiLatencySummary,
    build_latency_sample,
    summarize_latency,
    build_oad_018_certification_manifest,
    verify_oad_018_kalshi_end_to_end_latency_telemetry,
)

# OAD-019 exports
from .oad_019_hot_active_routing import (
    OAD_019_BUILD_ID,
    OAD_019_REVISION,
    ROUTING_TIERS,
    KalshiRoutingDecision,
    route_market,
    build_oad_019_certification_manifest,
    verify_oad_019_kalshi_hot_active_surveillance_routing,
)

# OAD-020 exports
from .oad_020_runtime_binding_gate import (
    OAD_020_BUILD_ID,
    OAD_020_REVISION,
    KalshiRuntimeBindingCertification,
    certify_oad_016_through_020,
    build_oad_020_certification_manifest,
    verify_oad_020_kalshi_production_streaming_runtime_binding_gate,
)

# OAD-021 exports
from .oad_021_credentials import (
    OAD_021_BUILD_ID,
    OAD_021_REVISION,
    KalshiCredentialConfig,
    load_kalshi_credentials,
    redact_credential_config,
    verify_oad_021_physical_kalshi_credential_auth_loader,
)

# OAD-022 exports
from .oad_022_rest_transport import (
    OAD_022_BUILD_ID,
    OAD_022_REVISION,
    KalshiRestResponse,
    build_auth_headers,
    kalshi_rest_get,
    build_oad_022_certification_manifest,
    verify_oad_022_physical_kalshi_rest_transport,
)

# OAD-023 exports
from .oad_023_real_universe_acquisition import (
    OAD_023_BUILD_ID,
    OAD_023_REVISION,
    RealKalshiUniverseAcquisition,
    acquire_real_kalshi_universe,
    build_oad_023_certification_manifest,
    verify_oad_023_real_kalshi_full_universe_acquisition,
)

# OAD-024 exports
from .oad_024_physical_websocket import (
    OAD_024_BUILD_ID,
    OAD_024_REVISION,
    KalshiWebSocketProbe,
    probe_kalshi_websocket,
    build_oad_024_certification_manifest,
    verify_oad_024_physical_kalshi_websocket_activation,
)

# OAD-025 exports
from .oad_025_live_acquisition_gate import (
    OAD_025_BUILD_ID,
    OAD_025_REVISION,
    LiveKalshiAcquisitionResult,
    run_live_kalshi_acquisition_probe,
    build_oad_025_certification_manifest,
    verify_oad_025_live_kalshi_acquisition_certification_gate,
)

# OAD-026 exports
from .oad_026_persistent_stream_runner import (
    OAD_026_BUILD_ID,
    OAD_026_REVISION,
    KalshiPersistentStreamConfig,
    KalshiPersistentStreamState,
    build_persistent_stream_config,
    next_reconnect_delay,
    verify_oad_026_persistent_kalshi_live_stream_runner,
)

# OAD-027 exports
from .oad_027_event_intake_pump import (
    OAD_027_BUILD_ID,
    OAD_027_REVISION,
    PumpResult,
    pump_market_messages,
    verify_oad_027_continuous_real_market_event_intake_pump,
)

# OAD-028 exports
from .oad_028_live_shadow_binding import (
    OAD_028_BUILD_ID,
    OAD_028_REVISION,
    LiveShadowPersistenceRecord,
    build_live_shadow_persistence_record,
    persistence_ready,
    verify_oad_028_live_shadow_postgres_persistence_binding,
)

# OAD-029 exports
from .oad_029_runtime_health import (
    OAD_029_BUILD_ID,
    OAD_029_REVISION,
    KalshiRuntimeHealth,
    evaluate_runtime_health,
    verify_oad_029_oracle_runtime_adapter_health_latency_supervision,
)

# OAD-030 exports
from .oad_030_runtime_integration_gate import (
    OAD_030_BUILD_ID,
    OAD_030_REVISION,
    KalshiOracleRuntimeIntegrationCertification,
    certify_oad_026_through_030,
    verify_oad_030_kalshi_oracle_live_runtime_integration_gate,
)

# OAD-031 exports
from .oad_031_runtime_binding import (
    OAD_031_BUILD_ID,
    OAD_031_REVISION,
    OracleKalshiRuntimeBinding,
    discover_live_shadow_launcher,
    build_oracle_kalshi_runtime_binding,
    verify_oad_031_physical_oracle_live_runtime_kalshi_binding,
)

# OAD-032 exports
from .oad_032_persistent_live_loop import (
    OAD_032_BUILD_ID,
    OAD_032_REVISION,
    PersistentKalshiLoopSummary,
    run_persistent_kalshi_loop,
    verify_oad_032_persistent_real_kalshi_message_loop,
)

# OAD-033 exports
from .oad_033_persistence_verification import (
    OAD_033_BUILD_ID,
    OAD_033_REVISION,
    LiveShadowPersistenceDiagnostic,
    discover_persistence_diagnostic,
    run_existing_persistence_diagnostic,
    verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification,
)

# OAD-034 exports
from .oad_034_runtime_status import (
    OAD_034_BUILD_ID,
    OAD_034_REVISION,
    OracleKalshiStatus,
    build_oracle_kalshi_status,
    verify_oad_034_runtime_kalshi_status_surface,
)

# OAD-035 exports
from .oad_035_physical_activation_gate import (
    OAD_035_BUILD_ID,
    OAD_035_REVISION,
    PhysicalOracleKalshiActivationCertification,
    certify_oad_031_through_035,
    verify_oad_035_physical_oracle_kalshi_production_activation_gate,
)

# OAD-036 exports
from .oad_036_websocket_canonical_bridge import (
    OAD_036_BUILD_ID,
    OAD_036_REVISION,
    SOURCE_ID,
    ADAPTER_ID,
    build_ola_canonical_observation_from_websocket,
    verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge,
)

# OAD-037 exports
from .oad_037_ola_postgres_router_binding import (
    OAD_037_BUILD_ID,
    OAD_037_REVISION,
    load_repository_environment,
    build_ola_production_persistence_router,
    persist_canonical_observation,
    verify_oad_037_ola_production_postgresql_router_binding,
)

# OAD-038 exports
from .oad_038_persistent_persistence_bridge import (
    OAD_038_BUILD_ID,
    OAD_038_REVISION,
    KalshiPersistenceBridgeSummary,
    run_kalshi_persistence_bridge,
    verify_oad_038_persistent_kalshi_to_postgresql_bridge,
)

# OAD-039 exports
from .oad_039_live_persistence_evidence import (
    OAD_039_BUILD_ID,
    OAD_039_REVISION,
    LivePersistenceEvidence,
    build_live_persistence_evidence,
    verify_oad_039_end_to_end_live_persistence_evidence,
)

# OAD-040 exports
from .oad_040_canonical_persistence_gate import (
    OAD_040_BUILD_ID,
    OAD_040_REVISION,
    KalshiCanonicalPersistenceCertification,
    certify_oad_036_through_040,
    verify_oad_040_kalshi_canonical_persistence_bridge_gate,
)

# OAD-041 exports
from .oad_041_full_universe_partitioning import (
    OAD_041_BUILD_ID,
    OAD_041_REVISION,
    FullUniverseStreamPartition,
    FullUniversePartitionPlan,
    build_full_universe_partition_plan,
    verify_oad_041_full_universe_stream_partition_expansion,
)

# OAD-042 exports
from .oad_042_partitioned_persistence import (
    OAD_042_BUILD_ID,
    OAD_042_REVISION,
    PartitionPersistenceState,
    build_partition_persistence_state,
    summarize_partition_persistence,
    verify_oad_042_partitioned_persistent_canonical_persistence,
)

# OAD-043 exports
from .oad_043_dynamic_intelligence_fanout import (
    OAD_043_BUILD_ID,
    OAD_043_REVISION,
    IntelligenceFanoutDecision,
    route_intelligence_fanout,
    verify_oad_043_dynamic_surveillance_fanout,
)

# OAD-044 exports
from .oad_044_downstream_intelligence_fanout import (
    OAD_044_BUILD_ID,
    OAD_044_REVISION,
    DEFAULT_CONSUMERS,
    DownstreamIntelligenceEnvelope,
    build_downstream_intelligence_envelope,
    verify_oad_044_downstream_intelligence_fanout,
)

# OAD-045 exports
from .oad_045_full_universe_intelligence_gate import (
    OAD_045_BUILD_ID,
    OAD_045_REVISION,
    FullUniverseLiveIntelligenceCertification,
    certify_oad_041_through_045,
    verify_oad_045_full_universe_live_intelligence_capability_gate,
)

# OAD-046 exports
from .oad_046_live_universe_enumeration import (
    OAD_046_BUILD_ID,
    OAD_046_REVISION,
    LiveUniverseEnumeration,
    enumerate_live_open_universe,
    verify_oad_046_physical_live_full_universe_enumeration,
)

# OAD-047 exports
from .oad_047_physical_coverage_plan import (
    OAD_047_BUILD_ID,
    OAD_047_REVISION,
    PhysicalCoveragePlan,
    build_physical_coverage_plan,
    verify_oad_047_global_fast_lane_and_orderbook_partition_plan,
)

# OAD-048 exports
from .oad_048_multi_partition_runtime import (
    OAD_048_BUILD_ID,
    OAD_048_REVISION,
    MultiPartitionRuntimeSummary,
    run_physical_multi_partition_persistence,
    build_kalshi_subscription_command,
    verify_oad_048_physical_multi_partition_persistence_runtime,
)

# OAD-049 exports
from .oad_049_full_universe_coverage_evidence import (
    OAD_049_BUILD_ID,
    OAD_049_REVISION,
    FullUniverseCoverageEvidence,
    build_full_universe_coverage_evidence,
    verify_oad_049_live_full_universe_coverage_evidence,
)

# OAD-050 exports
from .oad_050_physical_full_universe_gate import (
    OAD_050_BUILD_ID,
    OAD_050_REVISION,
    PhysicalFullUniverseRuntimeCertification,
    certify_oad_046_through_050,
    verify_oad_050_physical_full_universe_runtime_gate,
)

# OAD-051 exports
from .oad_051_adaptive_orderbook_tier_scheduler import (
    OAD_051_BUILD_ID,
    OAD_051_REVISION,
    TIER_PRIORITY,
    OrderbookTierPlan,
    build_adaptive_orderbook_tier_plan,
    verify_oad_051_adaptive_orderbook_tier_scheduler,
)

# OAD-052 exports
from .oad_052_dynamic_orderbook_rotation import (
    OAD_052_BUILD_ID,
    OAD_052_REVISION,
    SubscriptionRotation,
    compute_subscription_rotation,
    build_update_subscription_command,
    build_rotation_commands,
    verify_oad_052_dynamic_orderbook_partition_rotation,
)

# OAD-053 exports
from .oad_053_background_universe_inventory import (
    OAD_053_BUILD_ID,
    OAD_053_REVISION,
    UniverseInventoryCheckpoint,
    load_inventory_checkpoint,
    save_inventory_checkpoint,
    run_inventory_slice,
    verify_oad_053_incremental_background_universe_inventory,
)

# OAD-054 exports
from .oad_054_continuous_runtime_binding import (
    OAD_054_BUILD_ID,
    OAD_054_REVISION,
    ContinuousRuntimeBinding,
    build_continuous_runtime_binding,
    verify_oad_054_continuous_full_universe_runtime_binding,
)

# OAD-055 exports
from .oad_055_kalshi_production_freeze import (
    OAD_055_BUILD_ID,
    OAD_055_REVISION,
    KalshiProductionAdapterFreeze,
    certify_oad_051_through_055,
    verify_oad_055_kalshi_production_adapter_freeze_gate,
)
