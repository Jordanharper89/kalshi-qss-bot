"""Bounded physical observer gate; never launches or modifies the Oracle producer."""
from pathlib import Path
import time
from .ooi_015_verified_slop_evidence_snapshot import PREDICTIONS, RESOLUTIONS
from .ooi_021_existing_oos_observation_cycle import OpportunityOperatingSystem
from .ooi_022_restart_safe_observation_session import OpportunityObservationSession

EXECUTION_AUTHORITY = False

def source_signature(root):
    return tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in
                 (Path(root) / PREDICTIONS, Path(root) / RESOLUTIONS))

def summarize_observation(reports):
    accepted_ids = sorted({d['prediction_id'] for r in reports for d in r['decisions']
                           if d['status'] == 'RESEARCH_ACCEPTED'})
    held = sorted({reason for r in reports for d in r['decisions']
                   for reason in d.get('reasons', []) + d.get('validation_failed_checks', [])})
    if reports and not any(r.get('fresh_candidates', 0) for r in reports) and not accepted_ids:
        held = sorted(set(held + ['NO_FRESH_UNRESOLVED_CANDIDATES_OBSERVED']))
    if any(r['execution_authority'] is not False or r['read_only'] is not True for r in reports):
        raise ValueError('Read-only authority boundary failed')
    return dict(status='LIVE_RESEARCH_HANDOFF_OBSERVED' if accepted_ids else 'HOLD_NO_LIVE_ADMISSION',
        live_nonempty_certified=bool(accepted_ids), accepted_prediction_ids=accepted_ids,
        unique_accepted_count=len(accepted_ids), cycle_count=len(reports), hold_reasons=held,
        active_owned_count=reports[-1]['active_owned_count'] if reports else 0,
        execution_authority=False, read_only=True, launcher_modified=False,
        continuous_runtime_activation_certified=False, calibrated_probability_available=False)

def run_live_gate(root=None, duration_seconds=90, progress=print):
    if not isinstance(duration_seconds, (int, float)) or not 1 <= duration_seconds <= 180:
        raise ValueError('Physical gate duration must be between 1 and 180 seconds')
    root = Path(root or Path.cwd()).resolve()
    session = OpportunityObservationSession(root, OpportunityOperatingSystem())
    reports = [session.start()]
    progress('[LIVE_CYCLE] ' + str({k:reports[-1][k] for k in ('fresh_candidates','accepted','held','active_owned_count')}))
    started = time.monotonic()
    last_step = started
    last_progress = started
    signature = source_signature(root)
    # Local file-state checks only; no network/REST polling or acquisition duplication.
    while time.monotonic() - started < duration_seconds:
        remaining = duration_seconds - (time.monotonic() - started)
        if remaining <= 0:
            break
        time.sleep(min(2.0, remaining))
        now = time.monotonic()
        observed = source_signature(root)
        if observed != signature or now - last_step >= 10:
            report = session.step()
            reports.append(report)
            signature = observed
            last_step = now
        if now - last_progress >= 15:
            r = reports[-1]
            progress('[LIVE_PROGRESS] elapsed=%ds fresh=%d accepted=%d held=%d active=%d' %
                     (int(now-started),r['fresh_candidates'],r['accepted'],r['held'],r['active_owned_count']))
            last_progress = now
    reports.append(session.step())
    return summarize_observation(reports)
