"""One read-only observation cycle using the existing source ledger and OOS."""
from datetime import timedelta
from pathlib import Path
from .ooi_015_verified_slop_evidence_snapshot import PREDICTIONS, RESOLUTIONS, thesis_matches, timestamp, utc_now
from .ooi_020_pre_freeze_snapshot_selection import archived_snapshots, select_pre_freeze_snapshot
from .ooi_007b_slop_existing_oos_intake import OpportunityOperatingSystem, process_evidence_backed_slop

EXECUTION_AUTHORITY = False

def read_current_sources(root):
    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
    paths = [root / PREDICTIONS, root / RESOLUTIONS]
    before = [p.read_bytes() for p in paths]
    predictions = read_predictions(root)
    resolutions = read_resolution_dicts(root)
    if before != [p.read_bytes() for p in paths]:
        raise RuntimeError('Source ledgers changed during observation cycle')
    return predictions, {str(r['prediction_id']) for r in resolutions}

def is_owned_record(record):
    op = record.opportunity
    return (getattr(op, 'read_only', None) is True and
            op.metadata.get('source_revision') == 'SLOP_078B' and
            op.metadata.get('execution_authority') is False and
            'historical_evidence' in op.metadata)

def observation_cycle(root, oos, evaluated_at=None, policy=None):
    if not isinstance(oos, OpportunityOperatingSystem):
        raise TypeError('Caller-owned existing OOS required')
    root = Path(root).resolve()
    now = timestamp(evaluated_at or utc_now())
    predictions, resolved_ids = read_current_sources(root)
    snapshots = archived_snapshots(root)
    source_ids = {str(p.prediction_id) for p in predictions}
    removed = []
    for record in list(oos.all_records()):
        if not is_owned_record(record):
            continue
        op = record.opportunity
        expiry = timestamp(op.time_window.valid_until)
        reason = ('RESOLVED' if op.opportunity_id in resolved_ids else
                  'EXPIRED' if now >= expiry else
                  'SOURCE_PREDICTION_MISSING' if op.opportunity_id not in source_ids else None)
        if reason:
            oos.remove(record.fingerprint)
            removed.append({'opportunity_id': op.opportunity_id, 'reason': reason})
    decisions = []
    totals = {'fresh_candidates': 0, 'accepted': 0, 'registered': 0, 'duplicates': 0,
              'held': 0, 'expired_skipped': 0, 'resolved_skipped': 0, 'future_skipped': 0}
    for op in sorted(predictions, key=lambda p: (timestamp(p.frozen_at), str(p.prediction_id))):
        pid = str(op.prediction_id)
        if pid in resolved_ids:
            totals['resolved_skipped'] += 1
            continue
        start = timestamp(op.frozen_at)
        if now < start:
            totals['future_skipped'] += 1
            continue
        if now >= start + timedelta(seconds=60):
            totals['expired_skipped'] += 1
            continue
        totals['fresh_candidates'] += 1
        if not thesis_matches(op):
            totals['held'] += 1
            decisions.append({'prediction_id': pid, 'status': 'HOLD', 'reasons': ['THESIS_MISMATCH']})
            continue
        snapshot, reason = select_pre_freeze_snapshot(op.frozen_at, snapshots, policy)
        if snapshot is None:
            totals['held'] += 1
            decisions.append({'prediction_id': pid, 'status': 'HOLD', 'reasons': [reason]})
            continue
        result = process_evidence_backed_slop([op], snapshot, oos, policy=policy, evaluated_at=now.isoformat())
        pipe = result['pipeline']
        admitted = result['accepted_count']
        totals['accepted'] += admitted
        totals['registered'] += pipe.registered_count
        totals['duplicates'] += pipe.duplicate_count
        totals['held'] += 1 - admitted
        failed_checks = [c.check_id for report in result['validation_reports'] for c in report.checks
                         if not c.passed and getattr(c.severity, 'value', c.severity) == 'fail']
        decisions.append({'prediction_id': pid, 'status': 'RESEARCH_ACCEPTED' if admitted else 'HOLD',
            'snapshot_hash': snapshot.snapshot_hash, 'snapshot_captured_at': snapshot.captured_at,
            'frozen_at': str(op.frozen_at), 'validation_failed_checks': failed_checks,
            'reasons': [reason for held in result['held'] for reason in held['reasons']]})
    own_records = [r for r in oos.all_records() if is_owned_record(r)]
    return dict(totals, evaluated_at=now.isoformat(), source_prediction_count=len(predictions),
        retained_snapshot_count=len(snapshots), decisions=decisions, removed=removed,
        active_owned_count=len(own_records),
        active_owned_fingerprints=sorted(r.fingerprint for r in own_records),
        read_only=True, execution_authority=False)
