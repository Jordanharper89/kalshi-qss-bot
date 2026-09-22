"""As-of historical cohort statistics within the existing OOI subsystem."""
from dataclasses import dataclass, asdict
from datetime import timedelta
import math
from .ooi_015_verified_slop_evidence_snapshot import timestamp, thesis_matches, number, digest

@dataclass(frozen=True)
class EvidencePolicy:
    min_cases: int = 20
    min_tokens: int = 3
    max_history_seconds: int = 30 * 86400
    max_snapshot_age_seconds: int = 3600

    def validate(self):
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ValueError('Evidence policy values must be positive integers')
        if self.min_cases < 2 or self.min_tokens > self.min_cases:
            raise ValueError('Invalid sample policy')

def comparable_statistics(op, snapshot, policy=None):
    policy = policy or EvidencePolicy()
    policy.validate()
    if not thesis_matches(op):
        raise ValueError('Candidate differs from frozen thesis')
    rows = snapshot.rows()
    cutoff = timestamp(op.frozen_at)
    observed = timestamp(snapshot.captured_at)
    reasons = []
    if observed > cutoff:
        reasons.append('SNAPSHOT_NOT_KNOWN_AT_CANDIDATE_FREEZE')
    if (cutoff - observed).total_seconds() > policy.max_snapshot_age_seconds:
        reasons.append('STALE_EVIDENCE_SNAPSHOT')
    chosen = []
    token_end = {}
    seen = set()
    for e in sorted(rows, key=lambda x: (timestamp(x['frozen_at']), x['prediction_id'])):
        start = timestamp(e['frozen_at'])
        if e['original_conditions'] != dict(op.conditions or {}):
            continue
        if e['prediction_id'] == str(op.prediction_id) or e['token_address'] == str(op.token_address):
            continue
        if start + timedelta(seconds=60) > observed or start >= cutoff:
            continue
        if (cutoff - start).total_seconds() > policy.max_history_seconds:
            continue
        if e['opportunity_key'] in seen:
            continue
        if start < token_end.get(e['token_address'], start):
            continue
        seen.add(e['opportunity_key'])
        token_end[e['token_address']] = start + timedelta(seconds=60)
        chosen.append(e)
    if reasons:
        chosen = []
    n = len(chosen)
    tokens = len({e['token_address'] for e in chosen})
    values = [number(e['net_return']) for e in chosen]
    mean = math.fsum(values) / n if n else None
    positive = sum(x > 0 for x in values)
    frequency = positive / n if n else None
    # Descriptive Wilson score bound, not calibrated forecast probability.
    z = 1.959963984540054
    lower = ((frequency + z*z/(2*n) - z*math.sqrt(frequency*(1-frequency)/n + z*z/(4*n*n))) / (1+z*z/n)) if n else None
    if n < policy.min_cases:
        reasons.append('INSUFFICIENT_COMPARABLE_CASES')
    if tokens < policy.min_tokens:
        reasons.append('INSUFFICIENT_TOKEN_BREADTH')
    if mean is None or mean <= 0:
        reasons.append('NO_POSITIVE_HISTORICAL_NET_EDGE')
    body = dict(candidate_id=str(op.prediction_id), candidate_frozen_at=str(op.frozen_at),
        snapshot_hash=snapshot.snapshot_hash, snapshot_captured_at=snapshot.captured_at,
        policy=asdict(policy), case_count=n, token_count=tokens,
        historical_mean_net_return=mean, positive_net_frequency=frequency,
        historical_positive_net_wilson_lower=lower, eligible=not reasons,
        reasons=reasons, evidence_hashes=[e['evidence_hash'] for e in chosen],
        supporting_prediction_ids=[e['prediction_id'] for e in chosen],
        confidence_basis='DESCRIPTIVE_HISTORICAL_POSITIVE_NET_WILSON_LOWER',
        calibrated_probability_available=False, forecast_probability=None,
        sample_independence_certified=False, cross_token_dependence_evaluated=False,
        friction_already_deducted=True, execution_authority=False)
    body['statistics_hash'] = digest(body)
    return body
