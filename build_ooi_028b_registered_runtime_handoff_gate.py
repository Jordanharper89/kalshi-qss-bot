"""Install into the existing Oracle subsystem; stop on physical failure."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
FILES={'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_028_registered_runtime_handoff_gate.py': '"""Bounded gate reads the existing child\'s heartbeat; never starts a producer."""\nfrom pathlib import Path\nimport json\nimport time\nfrom .ooi_015_verified_slop_evidence_snapshot import timestamp, utc_now\nfrom .ooi_026_registered_child_observation import STATUS\n\nEXECUTION_AUTHORITY=False\n\ndef summarize(samples, now):\n    valid=[]\n    for sample in samples:\n        if sample.get(\'revision\')!=\'OOI_026\' or sample.get(\'child\')!=\'run_slop_buy_pressure_live.py\':\n            raise ValueError(\'Unexpected runtime status contract\')\n        if sample.get(\'execution_authority\') is not False or sample.get(\'read_only\') is not True:\n            raise ValueError(\'Runtime authority boundary failed\')\n        age=(timestamp(now)-timestamp(sample[\'updated_at\'])).total_seconds()\n        if 0<=age<=120: valid.append(sample)\n    completed=[s for s in valid if s[\'state\']==\'PRODUCER_AND_OBSERVER_HEALTHY\']\n    sequences={(s[\'pid\'],s[\'round_count\']) for s in completed}\n    progressed=any(b[\'pid\']==a[\'pid\'] and b[\'round_count\']>a[\'round_count\']\n                   for a in valid for b in completed)\n    # Only a completed round newer than the first observed status proves activity in this window.\n    first=samples[0] if samples else None\n    admitted=[]\n    for s in completed:\n        if first is None or s[\'pid\']!=first[\'pid\'] or s[\'round_count\']<=first[\'round_count\']: continue\n        report=s.get(\'observation\') or {}\n        if report.get(\'execution_authority\') is not False or report.get(\'read_only\') is not True:\n            raise ValueError(\'Observation authority boundary failed\')\n        for d in report.get(\'decisions\',[]):\n            if d[\'status\']==\'RESEARCH_ACCEPTED\':\n                if timestamp(d[\'snapshot_captured_at\'])>timestamp(d[\'frozen_at\']):\n                    raise ValueError(\'Accepted candidate used future evidence\')\n                admitted.append(d[\'prediction_id\'])\n    ids=sorted(set(admitted))\n    latest=valid[-1] if valid else None\n    healthy=bool(latest and latest[\'state\']==\'PRODUCER_AND_OBSERVER_HEALTHY\')\n    reasons=[]\n    if not samples: reasons.append(\'NO_CHILD_HEARTBEAT_RESTART_EXISTING_ORACLE\')\n    elif not valid: reasons.append(\'STALE_OR_FUTURE_CHILD_HEARTBEAT\')\n    elif not healthy: reasons.append(\'LATEST_CHILD_STATE_\'+latest[\'state\'])\n    if not progressed: reasons.append(\'NO_COMPLETED_ROUND_PROGRESSION_IN_WINDOW\')\n    if not ids: reasons.append(\'NO_LIVE_NONEMPTY_RESEARCH_ADMISSION_IN_WINDOW\')\n    return dict(status=\'LIVE_RESEARCH_HANDOFF_OBSERVED\' if ids else \'HOLD_NO_LIVE_ADMISSION\',\n        producer_round_progress_observed=progressed, latest_child_state=latest[\'state\'] if latest else None,\n        completed_sequences_observed=len(sequences), accepted_prediction_ids=ids,\n        live_nonempty_certified=bool(ids), hold_reasons=reasons,\n        read_only=True,execution_authority=False,continuous_runtime_activation_certified=False,\n        calibrated_probability_available=False)\n\ndef run_gate(root=None, duration_seconds=30, progress=print):\n    if not 1<=duration_seconds<=60: raise ValueError(\'Gate duration must be 1..60 seconds\')\n    root=Path(root or Path.cwd()).resolve();path=root/STATUS\n    samples=[];start=time.monotonic();last_progress=start\n    while True:\n        if path.exists():\n            sample=json.loads(path.read_text(encoding=\'utf-8\'))\n            if not samples or sample!=samples[-1]: samples.append(sample)\n        elapsed=time.monotonic()-start\n        if elapsed>=duration_seconds: break\n        if time.monotonic()-last_progress>=5:\n            progress(\'[RUNTIME_PROGRESS] elapsed=%ds statuses=%d\'%(int(elapsed),len(samples)))\n            last_progress=time.monotonic()\n        time.sleep(min(1,duration_seconds-elapsed))\n    result=summarize(samples,utc_now())\n    report=root/\'OOI_028_REGISTERED_RUNTIME_HANDOFF_GATE.json\'\n    report.write_text(json.dumps(dict(result=result,samples=samples),indent=2,sort_keys=True),encoding=\'utf-8\')\n    progress(\'[REPORT] \'+str(report))\n    return result\n', 'test_ooi_028b_registered_runtime_handoff_gate.py': "import importlib\nimport json\nimport sys\nR=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_028_registered_runtime_handoff_gate')\n\ndef main():\n    now='2026-09-17T00:00:30+00:00'\n    base=dict(revision='OOI_026',child='run_slop_buy_pressure_live.py',pid=123,\n        updated_at=now,state='PRODUCER_AND_OBSERVER_HEALTHY',round_count=1,\n        read_only=True,execution_authority=False,\n        observation=dict(read_only=True,execution_authority=False,decisions=[]))\n    assert not R.summarize([],now)['live_nonempty_certified']\n    assert not R.summarize([base],now)['producer_round_progress_observed']\n    advanced=dict(base,round_count=2)\n    held=R.summarize([base,advanced],now)\n    assert held['producer_round_progress_observed'] and not held['live_nonempty_certified']\n    decision=dict(status='RESEARCH_ACCEPTED',prediction_id='fixture-only',\n        snapshot_captured_at='2026-09-17T00:00:00+00:00',frozen_at='2026-09-17T00:00:10+00:00')\n    advanced=dict(advanced,observation=dict(read_only=True,execution_authority=False,decisions=[decision]))\n    assert R.summarize([base,advanced],now)['live_nonempty_certified']\n    stale=dict(base,updated_at='2026-09-16T00:00:00+00:00')\n    assert not R.summarize([stale],now)['live_nonempty_certified']\n    try:R.summarize([dict(base,execution_authority=True)],now)\n    except ValueError:pass\n    else:raise AssertionError('Authority violation ignored')\n    print('[PASS] OOI-028 deterministic fresh/stale, progression, nonempty and authority gates')\n    if '--live' in sys.argv:\n        result=R.run_gate(duration_seconds=30)\n        print('[LIVE_RESULT] '+json.dumps(result,sort_keys=True))\n        if not result['live_nonempty_certified']:print('[HOLD] Return the JSON report; no admission bypass')\n        print('[SCOPE] Bounded runtime observation; 24/7 activation remains uncertified')\n\nif __name__=='__main__':main()\n"}
PINS={'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_026_registered_child_observation.py': 'c4894df07fd523dc064f974cbb828590e53abd7ddb84ad0e03478fb3d91ffeb3', 'run_slop_buy_pressure_live.py': '70801e3a8ab3ee01a83fbfb16e140fac3cc17b183d9bc93b772ca749f46728dd'}
TEST='test_ooi_028b_registered_runtime_handoff_gate.py'
PREVIOUS='test_ooi_027b_registered_child_lifecycle_certification.py'

def require(ok,message):
    if not ok:raise RuntimeError(message)

def write(path,raw):
    temp=path.with_name(path.name+'.install.tmp')
    require(not temp.exists(),'Existing installation temporary file: '+str(temp))
    try:
        temp.write_bytes(raw);os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def clear_cache(path):
    cache=path.parent/'__pycache__'
    if cache.is_dir():
        for item in cache.glob(path.stem+'.*.pyc'):item.unlink()

def main():
    require((ROOT/PREVIOUS).is_file(),'Preceding certified test missing')
    for relative,expected in PINS.items():
        path=ROOT/relative
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,
                'Certified source differs: '+relative)
    original={}
    for relative,source in FILES.items():
        path=ROOT/relative
        require(path.parent.is_dir(),'Existing subsystem missing: '+str(path.parent))
        compile(source,str(path),'exec')
        original[relative]=path.read_bytes() if path.exists() else None
        require(relative in PINS or original[relative] is None or original[relative]==source.encode('utf-8'),
                'Existing target differs: '+relative)
    require(subprocess.run([sys.executable,'-B',str(ROOT/PREVIOUS)],cwd=str(ROOT)).returncode==0,
            'Preceding physical boundary failed; no files changed')
    changed=[]
    try:
        for relative,source in FILES.items():
            path=ROOT/relative
            require((path.read_bytes() if path.exists() else None)==original[relative],'Concurrent source change')
            write(path,source.encode('utf-8'));clear_cache(path);changed.append(relative)
        require(subprocess.run([sys.executable,'-B',str(ROOT/TEST)],cwd=str(ROOT)).returncode==0,
                'Installed deterministic test failed')
    except BaseException:
        for relative in reversed(changed):
            # Retain new tests as failure evidence; restore production changes.
            if relative==TEST:continue
            path=ROOT/relative
            if path.exists() and path.read_bytes()==FILES[relative].encode('utf-8'):
                if original[relative] is None:path.unlink()
                else:write(path,original[relative])
                clear_cache(path)
        print('[ROLLBACK] prior production sources restored; test retained',flush=True)
        raise
    print('[PASS] OOI-028B installed and physically tested; execution_authority=FALSE',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('[FAIL] OOI-028B: '+str(exc),flush=True)
        print('[STOP] Do not run the next installer; return full traceback/output',flush=True)
        raise
