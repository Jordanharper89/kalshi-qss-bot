"""Existing SLOP materializer, extended with verified historical evidence."""
from dataclasses import replace
from datetime import timedelta
from qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity import (
    UniversalOpportunity, OpportunityType, OpportunityDirection, OpportunityStatus,
    RiskLevel, OpportunityExecutionProfile, OpportunityTimeWindow, OpportunityEvidenceRef)
from .ooi_015_verified_slop_evidence_snapshot import timestamp, utc_now
from .ooi_016_asof_comparable_statistics import comparable_statistics

REVISION = 'OOI_017_EVIDENCE_BACKED_EXISTING_MATERIALIZER'
EXECUTION_AUTHORITY = False

def materialize_slop(op, evidence_snapshot=None, policy=None, evaluated_at=None):
    conditions = dict(op.conditions or {})
    base = UniversalOpportunity(opportunity_id=str(op.prediction_id), market_id=str(op.pair_address),
        market_type='SOLANA', venue_id='SOLANA', venue_name='Solana',
        opportunity_type=OpportunityType.UNKNOWN, direction=OpportunityDirection.BUY,
        expected_value=0.0, expected_edge=0.0, confidence=0.0,
        explanation='Prospective SLOP BUY_PRESSURE opportunity',
        supporting_prediction_ids=[str(op.prediction_id)], tags=['SLOP', 'BUY_PRESSURE', 'PROSPECTIVE'],
        raw_market={'token_address': str(op.token_address), 'pair_address': str(op.pair_address)},
        metadata={'source_revision': 'SLOP_078B', 'frozen_at': str(op.frozen_at), 'conditions': conditions,
            'horizon_seconds': op.horizon_seconds, 'target': op.target, 'stop': op.stop,
            'friction_bps': op.friction_bps, 'execution_authority': False},
        read_only=True, status=OpportunityStatus.NEW, risk_level=RiskLevel.UNKNOWN,
        execution=OpportunityExecutionProfile(required_execution_adapter='solana_wallet'))
    if evidence_snapshot is None:
        return base
    stats = comparable_statistics(op, evidence_snapshot, policy)
    now = timestamp(evaluated_at or utc_now())
    frozen = timestamp(op.frozen_at)
    end = frozen + timedelta(seconds=60)
    reasons = list(stats['reasons'])
    if now < frozen:
        reasons.append('CANDIDATE_FREEZE_IS_IN_FUTURE')
    if now >= end:
        reasons.append('CANDIDATE_EXPIRED')
    eligible = not reasons
    metadata = dict(base.metadata, historical_evidence=stats,
                    evidence_admission_eligible=eligible, evidence_hold_reasons=reasons,
                    evaluated_at=now.isoformat(), calibrated_probability_available=False,
                    execution_adapter_available=None, execution_adapter_invoked=False)
    references = [OpportunityEvidenceRef(evidence_id=h, source='SLOP_067',
        evidence_type='historical_prospective_net_return', created_at=evidence_snapshot.captured_at,
        summary='Historical outcome; 200 bps friction already deducted') for h in stats['evidence_hashes']]
    return replace(base,
        expected_value=stats['historical_mean_net_return'] if eligible else 0.0,
        expected_edge=stats['historical_mean_net_return'] if eligible else 0.0,
        confidence=stats['historical_positive_net_wilson_lower'] if eligible else 0.0,
        explanation=('Historical comparable-cohort net return estimate; descriptive confidence, '
                     'not a calibrated forecast probability.'),
        evidence_refs=references,
        supporting_prediction_ids=[str(op.prediction_id)] + stats['supporting_prediction_ids'],
        metadata=metadata, risk_flags=['UNCALIBRATED_HISTORICAL_ESTIMATE', 'ADAPTER_AVAILABILITY_UNVERIFIED'],
        time_window=OpportunityTimeWindow(discovered_at=frozen.isoformat(), valid_from=frozen.isoformat(),
            valid_until=end.isoformat(), estimated_lifetime_seconds=60,
            freshness_score=max(0.0, min(1.0, (end-now).total_seconds()/60))),
        created_at=frozen.isoformat(), updated_at=now.isoformat())
