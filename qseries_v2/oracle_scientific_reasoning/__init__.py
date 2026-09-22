"""Oracle Scientific Reasoning — deterministic read-only reasoning subsystem."""

# OSR-001 exports
from .osr_001_foundation import (
    OSR_001_BUILD_ID,
    OSR_001_REVISION,
    ScientificReasoningInput,
    build_scientific_reasoning_input,
    verify_scientific_reasoning_input,
    build_osr_001_certification_manifest,
    verify_osr_001_scientific_reasoning_foundation,
)

# OSR-002 exports
from .osr_002_hypothesis_formation import (
    OSR_002_BUILD_ID,
    OSR_002_REVISION,
    ScientificHypothesis,
    form_hypothesis,
    build_osr_002_certification_manifest,
    verify_osr_002_hypothesis_formation,
)

# OSR-003 exports
from .osr_003_evidence_evaluation import (
    OSR_003_BUILD_ID,
    OSR_003_REVISION,
    EvidenceItem,
    HypothesisEvidenceEvaluation,
    evaluate_hypothesis_evidence,
    build_osr_003_certification_manifest,
    verify_osr_003_evidence_evaluation,
)

# OSR-004 exports
from .osr_004_competing_hypotheses import (
    OSR_004_BUILD_ID,
    OSR_004_REVISION,
    CompetingHypothesisScore,
    CompetingHypothesisAnalysis,
    analyze_competing_hypotheses,
    build_osr_004_certification_manifest,
    verify_osr_004_competing_hypothesis_analysis,
)

# OSR-005 exports
from .osr_005_foundation_gate import (
    OSR_005_BUILD_ID,
    OSR_005_REVISION,
    ScientificReasoningFoundationCertification,
    certify_osr_001_through_005,
    build_osr_005_certification_manifest,
    verify_osr_005_foundation_hypothesis_evidence_certification_gate,
)

# OSR-006 exports
from .osr_006_bayesian_update import (
    OSR_006_BUILD_ID,
    OSR_006_REVISION,
    BayesianEvidenceUpdate,
    bayesian_update,
    sequential_bayesian_update,
    build_osr_006_certification_manifest,
    verify_osr_006_bayesian_belief_update_engine,
)

# OSR-007 exports
from .osr_007_causal_relationship import (
    OSR_007_BUILD_ID,
    OSR_007_REVISION,
    CausalCriterion,
    CausalRelationshipEvaluation,
    evaluate_causal_relationship,
    build_osr_007_certification_manifest,
    verify_osr_007_causal_relationship_evaluation,
)

# OSR-008 exports
from .osr_008_temporal_sequence import (
    OSR_008_BUILD_ID,
    OSR_008_REVISION,
    TemporalEvent,
    TemporalSequenceAnalysis,
    analyze_temporal_sequence,
    precedes,
    build_osr_008_certification_manifest,
    verify_osr_008_temporal_precedence_event_sequence_reasoning,
)

# OSR-009 exports
from .osr_009_reasoning_synthesis import (
    OSR_009_BUILD_ID,
    OSR_009_REVISION,
    ScientificSynthesis,
    synthesize_bayesian_causal_temporal,
    build_osr_009_certification_manifest,
    verify_osr_009_bayesian_causal_temporal_synthesis,
)

# OSR-010 exports
from .osr_010_bayesian_causal_temporal_gate import (
    OSR_010_BUILD_ID,
    OSR_010_REVISION,
    BayesianCausalTemporalCertification,
    certify_osr_006_through_010,
    build_osr_010_certification_manifest,
    verify_osr_010_bayesian_causal_temporal_certification_gate,
)

# OSR-011 exports
from .osr_011_uncertainty_decomposition import (
    OSR_011_BUILD_ID,
    OSR_011_REVISION,
    UncertaintyComponents,
    decompose_uncertainty,
    build_osr_011_certification_manifest,
    verify_osr_011_uncertainty_decomposition_engine,
)

# OSR-012 exports
from .osr_012_information_gain_priority import (
    OSR_012_BUILD_ID,
    OSR_012_REVISION,
    EvidenceCandidate,
    EvidencePriority,
    prioritize_evidence_candidates,
    build_osr_012_certification_manifest,
    verify_osr_012_information_gain_evidence_priority_engine,
)

# OSR-013 exports
from .osr_013_adversarial_challenge import (
    OSR_013_BUILD_ID,
    OSR_013_REVISION,
    HypothesisChallenge,
    AdversarialChallengeResult,
    challenge_hypothesis,
    build_osr_013_certification_manifest,
    verify_osr_013_adversarial_hypothesis_challenge_engine,
)

# OSR-014 exports
from .osr_014_alternative_synthesis import (
    OSR_014_BUILD_ID,
    OSR_014_REVISION,
    AlternativeExplanation,
    ContradictionAlternativeSynthesis,
    synthesize_alternatives,
    build_osr_014_certification_manifest,
    verify_osr_014_contradiction_alternative_explanation_synthesis,
)

# OSR-015 exports
from .osr_015_uncertainty_information_adversarial_gate import (
    OSR_015_BUILD_ID,
    OSR_015_REVISION,
    UncertaintyInformationAdversarialCertification,
    certify_osr_011_through_015,
    build_osr_015_certification_manifest,
    verify_osr_015_uncertainty_information_adversarial_certification_gate,
)

# OSR-016 exports
from .osr_016_decision_outcome_evaluation import (
    OSR_016_BUILD_ID,
    OSR_016_REVISION,
    OutcomeState,
    DecisionTheoreticEvaluation,
    evaluate_outcomes,
    build_osr_016_certification_manifest,
    verify_osr_016_decision_theoretic_outcome_evaluation,
)

# OSR-017 exports
from .osr_017_scenario_branching import (
    OSR_017_BUILD_ID,
    OSR_017_REVISION,
    ScenarioBranch,
    ScenarioTree,
    make_branch,
    build_scenario_tree,
    build_osr_017_certification_manifest,
    verify_osr_017_scenario_construction_branch_reasoning,
)

# OSR-018 exports
from .osr_018_counterfactual_reasoning import (
    OSR_018_BUILD_ID,
    OSR_018_REVISION,
    CounterfactualComparison,
    evaluate_counterfactual,
    require_identifiable_counterfactual,
    build_osr_018_certification_manifest,
    verify_osr_018_counterfactual_reasoning_engine,
)

# OSR-019 exports
from .osr_019_decision_scenario_counterfactual_synthesis import (
    OSR_019_BUILD_ID,
    OSR_019_REVISION,
    DecisionScenarioCounterfactualSynthesis,
    synthesize_decision_scenario_counterfactual,
    build_osr_019_certification_manifest,
    verify_osr_019_decision_scenario_counterfactual_synthesis,
)

# OSR-020 exports
from .osr_020_decision_scenario_counterfactual_gate import (
    OSR_020_BUILD_ID,
    OSR_020_REVISION,
    DecisionScenarioCounterfactualCertification,
    certify_osr_016_through_020,
    build_osr_020_certification_manifest,
    verify_osr_020_decision_scenario_counterfactual_certification_gate,
)

# OSR-021 exports
from .osr_021_strategic_agent_incentives import (
    OSR_021_BUILD_ID,
    OSR_021_REVISION,
    StrategicAgent,
    IncentiveAssessment,
    assess_incentive,
    rank_agent_actions,
    build_osr_021_certification_manifest,
    verify_osr_021_strategic_agent_incentive_reasoning,
)

# OSR-022 exports
from .osr_022_game_interaction import (
    OSR_022_BUILD_ID,
    OSR_022_REVISION,
    StrategyPayoff,
    GameInteraction,
    analyze_two_agent_game,
    build_osr_022_certification_manifest,
    verify_osr_022_game_theoretic_interaction_analysis,
)

# OSR-023 exports
from .osr_023_complex_system_emergence import (
    OSR_023_BUILD_ID,
    OSR_023_REVISION,
    SystemSignal,
    EmergentState,
    evaluate_emergent_state,
    build_osr_023_certification_manifest,
    verify_osr_023_complex_system_emergent_state_reasoning,
)

# OSR-024 exports
from .osr_024_signal_system_synthesis import (
    OSR_024_BUILD_ID,
    OSR_024_REVISION,
    DetectedSignal,
    StrategicSystemSignalSynthesis,
    synthesize_signal_system,
    build_osr_024_certification_manifest,
    verify_osr_024_signal_detection_strategic_system_synthesis,
)

# OSR-025 exports
from .osr_025_game_complex_signal_gate import (
    OSR_025_BUILD_ID,
    OSR_025_REVISION,
    GameComplexSignalCertification,
    certify_osr_021_through_025,
    build_osr_025_certification_manifest,
    verify_osr_025_game_complex_signal_certification_gate,
)

# OSR-026 exports
from .osr_026_reasoning_calibration import (
    OSR_026_BUILD_ID,
    OSR_026_REVISION,
    CalibrationObservation,
    CalibrationAssessment,
    assess_reasoning_calibration,
    build_osr_026_certification_manifest,
    verify_osr_026_reasoning_calibration_engine,
)

# OSR-027 exports
from .osr_027_meta_reasoning_quality import (
    OSR_027_BUILD_ID,
    OSR_027_REVISION,
    ReasoningQualityInput,
    MetaReasoningAssessment,
    evaluate_reasoning_quality,
    build_osr_027_certification_manifest,
    verify_osr_027_meta_reasoning_quality_evaluation,
)

# OSR-028 exports
from .osr_028_cross_capability_synthesis import (
    OSR_028_BUILD_ID,
    OSR_028_REVISION,
    CapabilityReasoningState,
    CrossCapabilitySynthesis,
    synthesize_capabilities,
    build_osr_028_certification_manifest,
    verify_osr_028_cross_capability_scientific_reasoning_synthesis,
)

# OSR-029 exports
from .osr_029_intelligence_state import (
    OSR_029_BUILD_ID,
    OSR_029_REVISION,
    OracleScientificIntelligenceState,
    build_oracle_scientific_intelligence_state,
    verify_oracle_scientific_intelligence_state,
    build_osr_029_certification_manifest,
    verify_osr_029_oracle_scientific_intelligence_state,
)

# OSR-030 exports
from .osr_030_final_freeze import (
    OSR_030_BUILD_ID,
    OSR_030_REVISION,
    ScientificReasoningFinalFreeze,
    certify_and_freeze_osr_001_through_030,
    build_osr_030_certification_manifest,
    verify_osr_030_scientific_reasoning_final_certification_freeze,
)
