"""ooi_016_asof_comparable_statistics: grounded in the supplied physical source contracts."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_016_asof_comparable_statistics.py'
TEST = ROOT / 'test_ooi_016_asof_comparable_statistics.py'
PREVIOUS = ROOT / 'test_ooi_015_verified_slop_evidence_snapshot.py'
EXPECTED = None
PINS = {}
MODULE_SOURCE = '"""As-of historical cohort statistics within the existing OOI subsystem."""\nfrom dataclasses import dataclass, asdict\nfrom datetime import timedelta\nimport math\nfrom .ooi_015_verified_slop_evidence_snapshot import timestamp, thesis_matches, number, digest\n\n@dataclass(frozen=True)\nclass EvidencePolicy:\n    min_cases: int = 20\n    min_tokens: int = 3\n    max_history_seconds: int = 30 * 86400\n    max_snapshot_age_seconds: int = 3600\n\n    def validate(self):\n        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):\n            raise ValueError(\'Evidence policy values must be positive integers\')\n        if self.min_cases < 2 or self.min_tokens > self.min_cases:\n            raise ValueError(\'Invalid sample policy\')\n\ndef comparable_statistics(op, snapshot, policy=None):\n    policy = policy or EvidencePolicy()\n    policy.validate()\n    if not thesis_matches(op):\n        raise ValueError(\'Candidate differs from frozen thesis\')\n    rows = snapshot.rows()\n    cutoff = timestamp(op.frozen_at)\n    observed = timestamp(snapshot.captured_at)\n    reasons = []\n    if observed > cutoff:\n        reasons.append(\'SNAPSHOT_NOT_KNOWN_AT_CANDIDATE_FREEZE\')\n    if (cutoff - observed).total_seconds() > policy.max_snapshot_age_seconds:\n        reasons.append(\'STALE_EVIDENCE_SNAPSHOT\')\n    chosen = []\n    token_end = {}\n    seen = set()\n    for e in sorted(rows, key=lambda x: (timestamp(x[\'frozen_at\']), x[\'prediction_id\'])):\n        start = timestamp(e[\'frozen_at\'])\n        if e[\'original_conditions\'] != dict(op.conditions or {}):\n            continue\n        if e[\'prediction_id\'] == str(op.prediction_id) or e[\'token_address\'] == str(op.token_address):\n            continue\n        if start + timedelta(seconds=60) > observed or start >= cutoff:\n            continue\n        if (cutoff - start).total_seconds() > policy.max_history_seconds:\n            continue\n        if e[\'opportunity_key\'] in seen:\n            continue\n        if start < token_end.get(e[\'token_address\'], start):\n            continue\n        seen.add(e[\'opportunity_key\'])\n        token_end[e[\'token_address\']] = start + timedelta(seconds=60)\n        chosen.append(e)\n    if reasons:\n        chosen = []\n    n = len(chosen)\n    tokens = len({e[\'token_address\'] for e in chosen})\n    values = [number(e[\'net_return\']) for e in chosen]\n    mean = math.fsum(values) / n if n else None\n    positive = sum(x > 0 for x in values)\n    frequency = positive / n if n else None\n    # Descriptive Wilson score bound, not calibrated forecast probability.\n    z = 1.959963984540054\n    lower = ((frequency + z*z/(2*n) - z*math.sqrt(frequency*(1-frequency)/n + z*z/(4*n*n))) / (1+z*z/n)) if n else None\n    if n < policy.min_cases:\n        reasons.append(\'INSUFFICIENT_COMPARABLE_CASES\')\n    if tokens < policy.min_tokens:\n        reasons.append(\'INSUFFICIENT_TOKEN_BREADTH\')\n    if mean is None or mean <= 0:\n        reasons.append(\'NO_POSITIVE_HISTORICAL_NET_EDGE\')\n    body = dict(candidate_id=str(op.prediction_id), candidate_frozen_at=str(op.frozen_at),\n        snapshot_hash=snapshot.snapshot_hash, snapshot_captured_at=snapshot.captured_at,\n        policy=asdict(policy), case_count=n, token_count=tokens,\n        historical_mean_net_return=mean, positive_net_frequency=frequency,\n        historical_positive_net_wilson_lower=lower, eligible=not reasons,\n        reasons=reasons, evidence_hashes=[e[\'evidence_hash\'] for e in chosen],\n        supporting_prediction_ids=[e[\'prediction_id\'] for e in chosen],\n        confidence_basis=\'DESCRIPTIVE_HISTORICAL_POSITIVE_NET_WILSON_LOWER\',\n        calibrated_probability_available=False, forecast_probability=None,\n        sample_independence_certified=False, cross_token_dependence_evaluated=False,\n        friction_already_deducted=True, execution_authority=False)\n    body[\'statistics_hash\'] = digest(body)\n    return body\n'
TEST_SOURCE = "import importlib\nimport tempfile\nfrom dataclasses import replace\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E\nS=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_016_asof_comparable_statistics')\n\ndef main():\n    with tempfile.TemporaryDirectory() as root:\n        fixture(root);snap=snapshot(root);op=candidate()\n        a=S.comparable_statistics(op,snap);b=S.comparable_statistics(op,snap)\n        require(a==b and a['eligible'] and a['case_count']==24,'positive cohort failed')\n        require(abs(a['historical_mean_net_return']-.055)<1e-12,'net edge incorrect/double friction')\n        require(0<a['historical_positive_net_wilson_lower']<a['positive_net_frequency']<1,'historical statistic invalid')\n        require(a['forecast_probability'] is None and not a['calibrated_probability_available'],'forecast falsely claimed')\n        future=S.comparable_statistics(candidate(frozen_at='2026-09-16T23:59:59+00:00'),snap)\n        require(not future['eligible'] and future['case_count']==0,'future snapshot leaked')\n        stale=S.comparable_statistics(candidate(frozen_at='2026-09-17T02:00:00+00:00'),snap)\n        require(not stale['eligible'],'stale snapshot admitted')\n        self_excluded=S.comparable_statistics(candidate(token_address='token_0'),snap)\n        require(self_excluded['case_count']==23,'same-token exclusion failed')\n        extra=S.comparable_statistics(candidate(conditions=(('order_flow','BUY_PRESSURE'),('other','X'))),snap)\n        require(extra['case_count']==0,'different condition cohort admitted')\n        rows=snap.rows();overlap=dict(rows[0]);overlap.update(prediction_id='overlap',opportunity_key='overlap',frozen_at='2026-09-16T23:00:30+00:00')\n        rows.append(overlap)\n        body=dict(captured_at=snap.captured_at, rows_json=E.canonical(rows), prediction_ledger_hash=snap.prediction_ledger_hash,\n            resolution_ledger_hash=snap.resolution_ledger_hash, execution_authority=False)\n        overlapped=E.EvidenceSnapshot(snapshot_hash=E.digest(body),**body)\n        require(S.comparable_statistics(op,overlapped)['case_count']==24,'overlap inflated sample')\n        fixture(root,count=2)\n        require(not S.comparable_statistics(op,snapshot(root))['eligible'],'small sample admitted')\n        fixture(root,gross=-.05)\n        require(not S.comparable_statistics(op,snapshot(root))['eligible'],'negative net edge admitted')\n        try:S.comparable_statistics(op,replace(snap,rows_json='[]'))\n        except ValueError:pass\n        else:raise AssertionError('tampered snapshot accepted')\n    print('[PASS] OOI-016 as-of cutoff, condition match, overlap/self exclusion, sample HOLD, friction once')\n    print('[POLICY] 20 cases / 3 tokens / 30 days history / snapshot age <= 1 hour')\n    print('[SCOPE] descriptive historical statistics; no calibrated forecast; execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def atomic(path, raw):
    temp = path.with_name(path.name + '.ooi_016_asof_comparable_statistics.tmp')
    require(not temp.exists(), 'Existing temporary file')
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def main():
    require(TARGET.parent.is_dir() and PREVIOUS.is_file(), 'Existing subsystem or preceding test missing')
    for rel, expected in PINS.items():
        path = ROOT / rel
        require(path.is_file() and sha(path.read_bytes()) == expected,
                'Captured source differs: ' + rel)
    require(subprocess.run([sys.executable, '-B', str(PREVIOUS)], cwd=str(ROOT)).returncode == 0,
            'Preceding physical test failed; no files changed')
    original = TARGET.read_bytes() if TARGET.exists() else None
    updated = MODULE_SOURCE.encode('utf-8')
    require((original is None and EXPECTED is None) or
            (original is not None and sha(original) in (EXPECTED, sha(updated))),
            'Target differs from known predecessor; refusing overwrite')
    if TEST.exists():
        require(TEST.read_text(encoding='utf-8') == TEST_SOURCE, 'Existing test differs; refusing overwrite')
    compile(MODULE_SOURCE, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    if original is not None:
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_016_asof_comparable_statistics_' + sha(original)[:12] + '.bak')
        require(not backup.exists() or backup.read_bytes() == original, 'Backup conflict')
        if not backup.exists():
            backup.write_bytes(original)
    if not TEST.exists():
        TEST.write_text(TEST_SOURCE, encoding='utf-8')
    changed = False
    try:
        require((TARGET.read_bytes() if TARGET.exists() else None) == original, 'Concurrent source change')
        atomic(TARGET, updated)
        changed = True
        clear_cache()
        require(subprocess.run([sys.executable, '-B', str(TEST)], cwd=str(ROOT)).returncode == 0,
                'Physical test failed')
    except BaseException:
        if changed and TARGET.exists() and TARGET.read_bytes() == updated:
            if original is None:
                TARGET.unlink()
            else:
                atomic(TARGET, original)
            clear_cache()
            print('[ROLLBACK] prior production boundary restored', flush=True)
        raise
    print('[PASS] OOI_016_ASOF_COMPARABLE_STATISTICS installed and tested; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_016_ASOF_COMPARABLE_STATISTICS: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return full output', flush=True)
        sys.exit(1)
