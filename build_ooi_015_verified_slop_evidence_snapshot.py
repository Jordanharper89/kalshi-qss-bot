"""ooi_015_verified_slop_evidence_snapshot: grounded in the supplied physical source contracts."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_015_verified_slop_evidence_snapshot.py'
TEST = ROOT / 'test_ooi_015_verified_slop_evidence_snapshot.py'
PREVIOUS = ROOT / 'test_ooi_013_slop_required_adapter_contract.py'
EXPECTED = None
PINS = {'qseries_v2/oracle_intelligence/universal_opportunity_model/universal_opportunity.py': '4b1b350f2d938955ebe89d33ef3408ae48d60bc1ac0bf616db5a7311582cb014', 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py': '09741e4fce9ac99a72fad5fbda771ce949b9f31a0bc83391aafa04c839cde9e2', 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_003_concurrent_opportunity_admission_prospective_freeze.py': '3320d6e2cd057e070071749247556245ea749931212cc04d5acd20ab0163472d', 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_013b_canonical_durable_prediction_ledger_rebuild.py': 'f9cdbbea39175fa3a955443bf80d6ce2caf0a1a992e82e4278cf04eabfa97948', 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_020_prospective_resolution_ledger.py': '30997466e1b25de3c22d5ac89e2baef3d9ef74e64105db5b5b41b2ad9013e263', 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_061_canonical_prospective_learning_evidence.py': '432307bb4bd4cac980d68fe4062f6e95badeebbf9211176432eae8248ba5acbf', 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_062_native_ocl_prospective_outcome_bridge.py': '7a717f00e22fac3afb7c4ed52b58bd7f1960b79f6d466b5839babc7f3ea80e2f', 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_067_opportunity_level_exactly_once_learning_lineage.py': 'de03fb13f6f5a0187be3ec078e94b985cce053b4e7b062a7157966345dce75b4'}
MODULE_SOURCE = '"""Verified, immutable SLOP evidence snapshots. No writer or execution calls."""\nfrom dataclasses import dataclass, asdict\nfrom datetime import datetime, timezone, timedelta\nfrom hashlib import sha256\nfrom pathlib import Path\nimport json\nimport math\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nPREDICTIONS = \'runtime_state/solana_live_opportunity/prospective_predictions.json\'\nRESOLUTIONS = \'runtime_state/solana_live_opportunity/economic_resolutions.json\'\n\ndef canonical(value):\n    return json.dumps(value, sort_keys=True, separators=(\',\', \':\'), allow_nan=False)\n\ndef digest(value):\n    return sha256(canonical(value).encode()).hexdigest()\n\ndef timestamp(value):\n    dt = datetime.fromisoformat(str(value).replace(\'Z\', \'+00:00\'))\n    if dt.tzinfo is None:\n        raise ValueError(\'Timezone-aware evidence timestamps required\')\n    return dt.astimezone(timezone.utc)\n\ndef utc_now():\n    return datetime.now(timezone.utc).isoformat()\n\ndef number(value):\n    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):\n        raise ValueError(\'Finite numeric evidence required\')\n    return float(value)\n\ndef thesis_matches(op):\n    return (dict(op.conditions or {}).get(\'order_flow\') == \'BUY_PRESSURE\'\n            and number(op.horizon_seconds) == 60 and number(op.target) == .10\n            and abs(number(op.stop)) == .05 and number(op.friction_bps) == 200\n            and getattr(op, \'execution_authority\', False) is False)\n\n@dataclass(frozen=True)\nclass EvidenceSnapshot:\n    captured_at: str\n    rows_json: str\n    prediction_ledger_hash: str\n    resolution_ledger_hash: str\n    snapshot_hash: str\n    execution_authority: bool = False\n\n    def rows(self):\n        body = asdict(self)\n        expected = body.pop(\'snapshot_hash\')\n        if self.execution_authority is not False or digest(body) != expected:\n            raise ValueError(\'Snapshot integrity/authority failure\')\n        timestamp(self.captured_at)\n        rows = json.loads(self.rows_json)\n        if not isinstance(rows, list):\n            raise ValueError(\'Snapshot row contract failure\')\n        return rows\n\ndef read_evidence_snapshot(root=None):\n    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions\n    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_067_opportunity_level_exactly_once_learning_lineage import independent_evidence, opportunity_key\n    root = Path(root or Path.cwd()).resolve()\n    paths = [root / PREDICTIONS, root / RESOLUTIONS]\n    if not all(p.is_file() for p in paths):\n        raise FileNotFoundError(\'Both existing SLOP ledgers are required; missing is not empty\')\n    before = [p.read_bytes() for p in paths]\n    documents = [json.loads(raw.decode(\'utf-8-sig\')) for raw in before]\n    predictions_raw = documents[0][\'predictions\']\n    resolutions_raw = documents[1][\'resolutions\']\n    for records in (predictions_raw, resolutions_raw):\n        ids = [str(r[\'prediction_id\']) for r in records]\n        if len(ids) != len(set(ids)):\n            raise ValueError(\'Duplicate ledger prediction_id; refusing silent overwrite\')\n    predictions = {p.prediction_id: p for p in read_predictions(root)}\n    resolutions = {str(r[\'prediction_id\']): r for r in resolutions_raw}\n    if set(resolutions) - set(predictions):\n        raise ValueError(\'Resolution missing original prediction lineage\')\n    selected = independent_evidence(root)\n    after = [p.read_bytes() for p in paths]\n    if before != after:\n        raise RuntimeError(\'Ledgers changed during snapshot; retry on next cycle\')\n    captured_at = utc_now()\n    captured = timestamp(captured_at)\n    rows = []\n    seen = set()\n    for key, original in selected:\n        e = dict(original)\n        pid = str(e[\'prediction_id\'])\n        p = predictions[pid]\n        r = resolutions[pid]\n        if not thesis_matches(p):\n            raise ValueError(\'Original prediction does not match frozen thesis: \' + pid)\n        if key != opportunity_key(e) or key in seen:\n            raise ValueError(\'Existing opportunity lineage key mismatch\')\n        seen.add(key)\n        expected_hash = e.pop(\'evidence_hash\')\n        if digest(e) != expected_hash:\n            raise ValueError(\'Canonical SLOP evidence hash mismatch\')\n        e[\'evidence_hash\'] = expected_hash\n        if any(e[k] != str(getattr(p, k)) for k in (\'token_address\', \'pair_address\', \'frozen_at\')):\n            raise ValueError(\'Prediction lineage mismatch\')\n        if not str(e[\'token_address\']).strip() or not str(e[\'pair_address\']).strip():\n            raise ValueError(\'Missing token/pair identity\')\n        if not isinstance(e[\'outcome\'], str) or not e[\'outcome\'].strip():\n            raise ValueError(\'Missing resolved outcome label\')\n        if number(r[\'friction_bps\']) != 200:\n            raise ValueError(\'Resolution friction differs from frozen thesis\')\n        gross, net = number(e[\'gross_return\']), number(e[\'net_return\'])\n        if not math.isclose(net, gross - .02, rel_tol=0, abs_tol=1e-9):\n            raise ValueError(\'Net return does not reconcile with 200 bps friction\')\n        if timestamp(e[\'frozen_at\']) + timedelta(seconds=60) > captured:\n            raise ValueError(\'Full historical horizon has not elapsed\')\n        if r.get(\'execution_authority\', False) is not False:\n            raise ValueError(\'Resolution authority mismatch\')\n        e[\'opportunity_key\'] = key\n        e[\'original_conditions\'] = dict(p.conditions)\n        rows.append(e)\n    rows.sort(key=lambda e: (timestamp(e[\'frozen_at\']), e[\'prediction_id\']))\n    body = dict(captured_at=captured_at, rows_json=canonical(rows),\n                prediction_ledger_hash=sha256(before[0]).hexdigest(),\n                resolution_ledger_hash=sha256(before[1]).hexdigest(), execution_authority=False)\n    return EvidenceSnapshot(snapshot_hash=digest(body), **body)\n'
TEST_SOURCE = "import copy\nimport importlib\nimport json\nfrom pathlib import Path\nimport tempfile\nfrom unittest.mock import patch\nfrom datetime import datetime, timezone, timedelta\n\nE = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_015_verified_slop_evidence_snapshot')\nP = importlib.import_module('qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze').ProspectiveOpportunity\nFIXED = '2026-09-17T00:00:00+00:00'\nCANDIDATE_TIME = '2026-09-17T00:00:10+00:00'\n\ndef require(value, message):\n    if not value:\n        raise AssertionError(message)\n\ndef fixture(root, count=24, gross=.10):\n    predictions, resolutions = [], []\n    for i in range(count):\n        pid = 'historical_' + str(i)\n        value = gross if i < 20 else -.05\n        predictions.append(dict(prediction_id=pid, token_address='token_'+str(i), pair_address='pair_'+str(i),\n            frozen_at='2026-09-16T23:00:00+00:00', conditions=[['order_flow','BUY_PRESSURE']],\n            horizon_seconds=60, target=.10, stop=.05, friction_bps=200,\n            state='PENDING_60S', execution_authority=False))\n        resolutions.append(dict(prediction_id=pid, outcome='TARGET_FIRST' if value>0 else 'STOP_FIRST',\n            gross_return=value, net_return=value-.02, terminal_return=value,\n            mfe=max(value,0), mae=min(value,0), friction_bps=200, execution_authority=False))\n    for relative, key, values in [(E.PREDICTIONS,'predictions',predictions),(E.RESOLUTIONS,'resolutions',resolutions)]:\n        path=Path(root)/relative;path.parent.mkdir(parents=True,exist_ok=True)\n        path.write_text(json.dumps({key:values}),encoding='utf-8')\n    return predictions, resolutions\n\ndef snapshot(root):\n    with patch.object(E,'utc_now',return_value=FIXED):\n        return E.read_evidence_snapshot(root)\n\ndef candidate(**changes):\n    values=dict(prediction_id='candidate', token_address='new_token', pair_address='new_pair',\n        frozen_at=CANDIDATE_TIME, conditions=(('order_flow','BUY_PRESSURE'),),\n        horizon_seconds=60, target=.10, stop=.05, friction_bps=200)\n    values.update(changes)\n    return P(**values)\n\ndef main():\n    with tempfile.TemporaryDirectory() as root:\n        ps, rs=fixture(root)\n        paths=[Path(root)/E.PREDICTIONS,Path(root)/E.RESOLUTIONS]\n        before=[p.read_bytes() for p in paths]\n        a=snapshot(root);b=snapshot(root)\n        require(a==b and len(a.rows())==24,'snapshot replay/count failed')\n        require([p.read_bytes() for p in paths]==before,'reader modified existing ledgers')\n        require(a.rows()[0]['original_conditions']=={'order_flow':'BUY_PRESSURE'},'original thesis not retained')\n        ps[0]['target']=.20\n        paths[0].write_text(json.dumps({'predictions':ps}))\n        try:snapshot(root)\n        except ValueError:pass\n        else:raise AssertionError('hardcoded upstream thesis masked original mismatch')\n        fixture(root)\n        ps,rs=fixture(root);rs[0]['net_return']=.10\n        paths[1].write_text(json.dumps({'resolutions':rs}))\n        try:snapshot(root)\n        except ValueError:pass\n        else:raise AssertionError('friction mismatch accepted')\n        ps,rs=fixture(root);ps.append(copy.deepcopy(ps[0]))\n        paths[0].write_text(json.dumps({'predictions':ps}))\n        try:snapshot(root)\n        except ValueError:pass\n        else:raise AssertionError('duplicate ledger id accepted')\n    print('[PASS] OOI-015 actual SLOP readers, hash/lineage validation, original thesis check, no ledger writes')\n    print('[SCOPE] Temporary deterministic fixtures; execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"

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
    temp = path.with_name(path.name + '.ooi_015_verified_slop_evidence_snapshot.tmp')
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
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_015_verified_slop_evidence_snapshot_' + sha(original)[:12] + '.bak')
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
    print('[PASS] OOI_015_VERIFIED_SLOP_EVIDENCE_SNAPSHOT installed and tested; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_015_VERIFIED_SLOP_EVIDENCE_SNAPSHOT: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return full output', flush=True)
        sys.exit(1)
