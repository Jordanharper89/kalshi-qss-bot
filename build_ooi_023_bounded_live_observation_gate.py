"""ooi_023_bounded_live_observation_gate: existing Oracle OOS live-observation boundary."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_023_bounded_live_observation_gate.py'
TEST = ROOT / 'test_ooi_023_bounded_live_observation_gate.py'
PREVIOUS = ROOT / 'test_ooi_022_restart_safe_observation_session.py'
PINS = {}
MODULE_SOURCE = '"""Bounded physical observer gate; never launches or modifies the Oracle producer."""\nfrom pathlib import Path\nimport time\nfrom .ooi_015_verified_slop_evidence_snapshot import PREDICTIONS, RESOLUTIONS\nfrom .ooi_021_existing_oos_observation_cycle import OpportunityOperatingSystem\nfrom .ooi_022_restart_safe_observation_session import OpportunityObservationSession\n\nEXECUTION_AUTHORITY = False\n\ndef source_signature(root):\n    return tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in\n                 (Path(root) / PREDICTIONS, Path(root) / RESOLUTIONS))\n\ndef summarize_observation(reports):\n    accepted_ids = sorted({d[\'prediction_id\'] for r in reports for d in r[\'decisions\']\n                           if d[\'status\'] == \'RESEARCH_ACCEPTED\'})\n    held = sorted({reason for r in reports for d in r[\'decisions\']\n                   for reason in d.get(\'reasons\', []) + d.get(\'validation_failed_checks\', [])})\n    if reports and not any(r.get(\'fresh_candidates\', 0) for r in reports) and not accepted_ids:\n        held = sorted(set(held + [\'NO_FRESH_UNRESOLVED_CANDIDATES_OBSERVED\']))\n    if any(r[\'execution_authority\'] is not False or r[\'read_only\'] is not True for r in reports):\n        raise ValueError(\'Read-only authority boundary failed\')\n    return dict(status=\'LIVE_RESEARCH_HANDOFF_OBSERVED\' if accepted_ids else \'HOLD_NO_LIVE_ADMISSION\',\n        live_nonempty_certified=bool(accepted_ids), accepted_prediction_ids=accepted_ids,\n        unique_accepted_count=len(accepted_ids), cycle_count=len(reports), hold_reasons=held,\n        active_owned_count=reports[-1][\'active_owned_count\'] if reports else 0,\n        execution_authority=False, read_only=True, launcher_modified=False,\n        continuous_runtime_activation_certified=False, calibrated_probability_available=False)\n\ndef run_live_gate(root=None, duration_seconds=90, progress=print):\n    if not isinstance(duration_seconds, (int, float)) or not 1 <= duration_seconds <= 180:\n        raise ValueError(\'Physical gate duration must be between 1 and 180 seconds\')\n    root = Path(root or Path.cwd()).resolve()\n    session = OpportunityObservationSession(root, OpportunityOperatingSystem())\n    reports = [session.start()]\n    progress(\'[LIVE_CYCLE] \' + str({k:reports[-1][k] for k in (\'fresh_candidates\',\'accepted\',\'held\',\'active_owned_count\')}))\n    started = time.monotonic()\n    last_step = started\n    last_progress = started\n    signature = source_signature(root)\n    # Local file-state checks only; no network/REST polling or acquisition duplication.\n    while time.monotonic() - started < duration_seconds:\n        remaining = duration_seconds - (time.monotonic() - started)\n        if remaining <= 0:\n            break\n        time.sleep(min(2.0, remaining))\n        now = time.monotonic()\n        observed = source_signature(root)\n        if observed != signature or now - last_step >= 10:\n            report = session.step()\n            reports.append(report)\n            signature = observed\n            last_step = now\n        if now - last_progress >= 15:\n            r = reports[-1]\n            progress(\'[LIVE_PROGRESS] elapsed=%ds fresh=%d accepted=%d held=%d active=%d\' %\n                     (int(now-started),r[\'fresh_candidates\'],r[\'accepted\'],r[\'held\'],r[\'active_owned_count\']))\n            last_progress = now\n    reports.append(session.step())\n    return summarize_observation(reports)\n'
TEST_SOURCE = "import importlib\nimport json\nimport sys\nfrom pathlib import Path\nfrom test_ooi_015_verified_slop_evidence_snapshot import require\nL=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_023_bounded_live_observation_gate')\n\ndef fixture_checks():\n    empty=dict(decisions=[],active_owned_count=0,read_only=True,execution_authority=False)\n    held=L.summarize_observation([empty])\n    require(not held['live_nonempty_certified'] and held['status']=='HOLD_NO_LIVE_ADMISSION','empty stream passed live gate')\n    accepted=dict(empty,decisions=[dict(prediction_id='fixture-only',status='RESEARCH_ACCEPTED',reasons=[])],active_owned_count=1)\n    report=L.summarize_observation([accepted,accepted])\n    require(report['unique_accepted_count']==1 and report['cycle_count']==2,'duplicate observation inflated admission')\n    require(report['continuous_runtime_activation_certified'] is False,'bounded gate claimed continuous runtime')\n    try:L.summarize_observation([dict(empty,execution_authority=True)])\n    except ValueError:pass\n    else:raise AssertionError('execution authority breach accepted')\n    print('[PASS] OOI-023 live-gate accounting tests; empty stream remains HOLD')\n\ndef physical_check():\n    print('[OBSERVE] Up to 90 seconds. Existing Oracle producer must supply fresh predictions; no producer is started here.',flush=True)\n    result=L.run_live_gate(Path(__file__).resolve().parent,duration_seconds=90)\n    print('[LIVE_RESULT]',json.dumps(result,sort_keys=True),flush=True)\n    if result['live_nonempty_certified']:\n        print('[PASS] NONEMPTY LIVE RESEARCH HANDOFF OBSERVED; execution_authority=FALSE',flush=True)\n    else:\n        print('[HOLD] No qualifying live handoff observed. Live nonempty certification remains pending.',flush=True)\n    print('[SCOPE] Bounded observation only; 24/7 activation is not certified.',flush=True)\n\nif __name__=='__main__':\n    fixture_checks()\n    if '--fixture-only' not in sys.argv:physical_check()\n"
INSTALL_TEST_ARGS = ['--fixture-only']

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def atomic(path, raw):
    temp = path.with_name(path.name + '.ooi_023_bounded_live_observation_gate.tmp')
    require(not temp.exists(), 'Existing temporary file')
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def main():
    require(TARGET.parent.is_dir() and PREVIOUS.is_file(), 'Existing subsystem or preceding test missing')
    for relative, expected in PINS.items():
        p = ROOT / relative
        require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == expected,
                'Certified source differs: ' + relative)
    require(subprocess.run([sys.executable, '-B', str(PREVIOUS)], cwd=str(ROOT)).returncode == 0,
            'Preceding boundary failed; no production files changed')
    original = TARGET.read_bytes() if TARGET.exists() else None
    updated = MODULE_SOURCE.encode('utf-8')
    require(original is None or original == updated, 'Target differs; refusing overwrite')
    if TEST.exists():
        require(TEST.read_text(encoding='utf-8') == TEST_SOURCE, 'Existing test differs; refusing overwrite')
    compile(MODULE_SOURCE, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    if not TEST.exists():
        TEST.write_text(TEST_SOURCE, encoding='utf-8')
    changed = False
    try:
        require((TARGET.read_bytes() if TARGET.exists() else None) == original, 'Concurrent source change')
        atomic(TARGET, updated)
        changed = True
        clear_cache()
        require(subprocess.run([sys.executable, '-B', str(TEST)] + INSTALL_TEST_ARGS, cwd=str(ROOT)).returncode == 0,
                'Deterministic installation test failed')
    except BaseException:
        if changed and TARGET.exists() and TARGET.read_bytes() == updated and original is None:
            TARGET.unlink()
            clear_cache()
            print('[ROLLBACK] newly installed module removed', flush=True)
        raise
    print('[PASS] OOI_023_BOUNDED_LIVE_OBSERVATION_GATE installed; deterministic checks passed', flush=True)
    print('[NEXT] Run ' + TEST.name + ' exactly as supplied; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_023_BOUNDED_LIVE_OBSERVATION_GATE: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return complete output', flush=True)
        sys.exit(1)
