"""Bounded gate reads the existing child's heartbeat; never starts a producer."""
from pathlib import Path
import json
import time
from .ooi_015_verified_slop_evidence_snapshot import timestamp, utc_now
from .ooi_026_registered_child_observation import STATUS

EXECUTION_AUTHORITY=False

def summarize(samples, now):
    valid=[]
    for sample in samples:
        if sample.get('revision')!='OOI_026' or sample.get('child')!='run_slop_buy_pressure_live.py':
            raise ValueError('Unexpected runtime status contract')
        if sample.get('execution_authority') is not False or sample.get('read_only') is not True:
            raise ValueError('Runtime authority boundary failed')
        age=(timestamp(now)-timestamp(sample['updated_at'])).total_seconds()
        if 0<=age<=120: valid.append(sample)
    completed=[s for s in valid if s['state']=='PRODUCER_AND_OBSERVER_HEALTHY']
    sequences={(s['pid'],s['round_count']) for s in completed}
    progressed=any(b['pid']==a['pid'] and b['round_count']>a['round_count']
                   for a in valid for b in completed)
    # Only a completed round newer than the first observed status proves activity in this window.
    first=samples[0] if samples else None
    admitted=[]
    for s in completed:
        if first is None or s['pid']!=first['pid'] or s['round_count']<=first['round_count']: continue
        report=s.get('observation') or {}
        if report.get('execution_authority') is not False or report.get('read_only') is not True:
            raise ValueError('Observation authority boundary failed')
        for d in report.get('decisions',[]):
            if d['status']=='RESEARCH_ACCEPTED':
                if timestamp(d['snapshot_captured_at'])>timestamp(d['frozen_at']):
                    raise ValueError('Accepted candidate used future evidence')
                admitted.append(d['prediction_id'])
    ids=sorted(set(admitted))
    latest=valid[-1] if valid else None
    healthy=bool(latest and latest['state']=='PRODUCER_AND_OBSERVER_HEALTHY')
    reasons=[]
    if not samples: reasons.append('NO_CHILD_HEARTBEAT_RESTART_EXISTING_ORACLE')
    elif not valid: reasons.append('STALE_OR_FUTURE_CHILD_HEARTBEAT')
    elif not healthy: reasons.append('LATEST_CHILD_STATE_'+latest['state'])
    if not progressed: reasons.append('NO_COMPLETED_ROUND_PROGRESSION_IN_WINDOW')
    if not ids: reasons.append('NO_LIVE_NONEMPTY_RESEARCH_ADMISSION_IN_WINDOW')
    return dict(status='LIVE_RESEARCH_HANDOFF_OBSERVED' if ids else 'HOLD_NO_LIVE_ADMISSION',
        producer_round_progress_observed=progressed, latest_child_state=latest['state'] if latest else None,
        completed_sequences_observed=len(sequences), accepted_prediction_ids=ids,
        live_nonempty_certified=bool(ids), hold_reasons=reasons,
        read_only=True,execution_authority=False,continuous_runtime_activation_certified=False,
        calibrated_probability_available=False)

def run_gate(root=None, duration_seconds=30, progress=print):
    if not 1<=duration_seconds<=60: raise ValueError('Gate duration must be 1..60 seconds')
    root=Path(root or Path.cwd()).resolve();path=root/STATUS
    samples=[];start=time.monotonic();last_progress=start
    while True:
        if path.exists():
            sample=json.loads(path.read_text(encoding='utf-8'))
            if not samples or sample!=samples[-1]: samples.append(sample)
        elapsed=time.monotonic()-start
        if elapsed>=duration_seconds: break
        if time.monotonic()-last_progress>=5:
            progress('[RUNTIME_PROGRESS] elapsed=%ds statuses=%d'%(int(elapsed),len(samples)))
            last_progress=time.monotonic()
        time.sleep(min(1,duration_seconds-elapsed))
    result=summarize(samples,utc_now())
    report=root/'OOI_028_REGISTERED_RUNTIME_HANDOFF_GATE.json'
    report.write_text(json.dumps(dict(result=result,samples=samples),indent=2,sort_keys=True),encoding='utf-8')
    progress('[REPORT] '+str(report))
    return result
