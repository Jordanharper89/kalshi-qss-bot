"""ooi_022_restart_safe_observation_session: existing Oracle OOS live-observation boundary."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_022_restart_safe_observation_session.py'
TEST = ROOT / 'test_ooi_022_restart_safe_observation_session.py'
PREVIOUS = ROOT / 'test_ooi_021_existing_oos_observation_cycle.py'
PINS = {}
MODULE_SOURCE = '"""Reusable observation session; restart reconstructs the existing OOS from source evidence."""\nfrom pathlib import Path\nfrom .ooi_015_verified_slop_evidence_snapshot import PREDICTIONS, RESOLUTIONS, timestamp, utc_now\nfrom .ooi_019_retained_evidence_snapshot import capture_and_retain\nfrom .ooi_021_existing_oos_observation_cycle import observation_cycle, OpportunityOperatingSystem\n\nEXECUTION_AUTHORITY = False\n\nclass OpportunityObservationSession:\n    def __init__(self, root, oos, policy=None):\n        if not isinstance(oos, OpportunityOperatingSystem):\n            raise TypeError(\'Pass the existing caller-owned OpportunityOperatingSystem\')\n        self.root = Path(root).resolve()\n        self.oos = oos\n        self.policy = policy\n        self.last_capture_at = None\n        self.resolution_signature = None\n        self.started = False\n\n    def _resolution_signature(self):\n        s = (self.root / RESOLUTIONS).stat()\n        return s.st_mtime_ns, s.st_size\n\n    def refresh_evidence(self):\n        signature_before = self._resolution_signature()\n        snapshot = capture_and_retain(self.root)\n        self.last_capture_at = snapshot.captured_at\n        # A concurrent resolution update triggers another capture on the next step.\n        self.resolution_signature = signature_before\n        return snapshot\n\n    def start(self, evaluated_at=None):\n        self.refresh_evidence()\n        report = observation_cycle(self.root, self.oos, evaluated_at=evaluated_at, policy=self.policy)\n        self.started = True\n        return report\n\n    def step(self, evaluated_at=None):\n        if not self.started:\n            raise RuntimeError(\'Call start() before step()\')\n        now = timestamp(evaluated_at or utc_now())\n        age = (now - timestamp(self.last_capture_at)).total_seconds()\n        if age < 0:\n            raise RuntimeError(\'Clock moved behind retained evidence capture\')\n        if age >= 60 or self._resolution_signature() != self.resolution_signature:\n            self.refresh_evidence()\n        return observation_cycle(self.root, self.oos, evaluated_at=now.isoformat(), policy=self.policy)\n'
TEST_SOURCE = "import importlib\nimport tempfile\nfrom unittest.mock import patch\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E,FIXED\nfrom test_ooi_019_retained_evidence_snapshot import A\nfrom test_ooi_021_existing_oos_observation_cycle import C,append_candidate\nfrom test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock\nR=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_022_restart_safe_observation_session')\n\ndef main():\n    with tempfile.TemporaryDirectory() as root, fixed_validation_clock(), patch.object(E,'utc_now',return_value=FIXED):\n        fixture(root);A.retain_snapshot(snapshot(root),root);append_candidate(root,candidate())\n        first=R.OpportunityObservationSession(root,C.OpportunityOperatingSystem())\n        a=first.start(evaluated_at='2026-09-17T00:00:20+00:00')\n        repeat=first.step(evaluated_at='2026-09-17T00:00:21+00:00')\n        require(a['active_owned_count']==1 and repeat['duplicates']==1,'session state not reused')\n        recovered=R.OpportunityObservationSession(root,C.OpportunityOperatingSystem())\n        b=recovered.start(evaluated_at='2026-09-17T00:00:21+00:00')\n        require(b['active_owned_fingerprints']==a['active_owned_fingerprints'],'restart changed active research identity')\n        old=R.OpportunityObservationSession(root,C.OpportunityOperatingSystem())\n        expired=old.start(evaluated_at='2026-09-17T00:01:11+00:00')\n        require(expired['active_owned_count']==0,'restart resurrected expired candidate')\n        try:recovered.step(evaluated_at='2026-09-16T23:59:00+00:00')\n        except RuntimeError:pass\n        else:raise AssertionError('clock rollback ignored')\n    print('[PASS] OOI-022 existing OOS session reuse, restart reconstruction, expiry exclusion, clock rollback guard')\n    print('[SCOPE] Fixture recovery; production launcher unchanged; execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"
INSTALL_TEST_ARGS = []

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def atomic(path, raw):
    temp = path.with_name(path.name + '.ooi_022_restart_safe_observation_session.tmp')
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
    print('[PASS] OOI_022_RESTART_SAFE_OBSERVATION_SESSION installed; deterministic checks passed', flush=True)
    print('[NEXT] Run ' + TEST.name + ' exactly as supplied; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_022_RESTART_SAFE_OBSERVATION_SESSION: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return complete output', flush=True)
        sys.exit(1)
