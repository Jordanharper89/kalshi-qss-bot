"""Verified, immutable SLOP evidence snapshots. No writer or execution calls."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import json
import math

EXECUTION_AUTHORITY = False
READ_ONLY = True
PREDICTIONS = 'runtime_state/solana_live_opportunity/prospective_predictions.json'
RESOLUTIONS = 'runtime_state/solana_live_opportunity/economic_resolutions.json'

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return sha256(canonical(value).encode()).hexdigest()

def timestamp(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timezone-aware evidence timestamps required')
    return dt.astimezone(timezone.utc)

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Finite numeric evidence required')
    return float(value)

def thesis_matches(op):
    return (dict(op.conditions or {}).get('order_flow') == 'BUY_PRESSURE'
            and number(op.horizon_seconds) == 60 and number(op.target) == .10
            and abs(number(op.stop)) == .05 and number(op.friction_bps) == 200
            and getattr(op, 'execution_authority', False) is False)

@dataclass(frozen=True)
class EvidenceSnapshot:
    captured_at: str
    rows_json: str
    prediction_ledger_hash: str
    resolution_ledger_hash: str
    snapshot_hash: str
    execution_authority: bool = False

    def rows(self):
        body = asdict(self)
        expected = body.pop('snapshot_hash')
        if self.execution_authority is not False or digest(body) != expected:
            raise ValueError('Snapshot integrity/authority failure')
        timestamp(self.captured_at)
        rows = json.loads(self.rows_json)
        if not isinstance(rows, list):
            raise ValueError('Snapshot row contract failure')
        return rows

def read_evidence_snapshot(root=None):
    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_067_opportunity_level_exactly_once_learning_lineage import independent_evidence, opportunity_key
    root = Path(root or Path.cwd()).resolve()
    paths = [root / PREDICTIONS, root / RESOLUTIONS]
    if not all(p.is_file() for p in paths):
        raise FileNotFoundError('Both existing SLOP ledgers are required; missing is not empty')
    before = [p.read_bytes() for p in paths]
    documents = [json.loads(raw.decode('utf-8-sig')) for raw in before]
    predictions_raw = documents[0]['predictions']
    resolutions_raw = documents[1]['resolutions']
    for records in (predictions_raw, resolutions_raw):
        ids = [str(r['prediction_id']) for r in records]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate ledger prediction_id; refusing silent overwrite')
    predictions = {p.prediction_id: p for p in read_predictions(root)}
    resolutions = {str(r['prediction_id']): r for r in resolutions_raw}
    if set(resolutions) - set(predictions):
        raise ValueError('Resolution missing original prediction lineage')
    selected = independent_evidence(root)
    after = [p.read_bytes() for p in paths]
    if before != after:
        raise RuntimeError('Ledgers changed during snapshot; retry on next cycle')
    captured_at = utc_now()
    captured = timestamp(captured_at)
    rows = []
    seen = set()
    for key, original in selected:
        e = dict(original)
        pid = str(e['prediction_id'])
        p = predictions[pid]
        r = resolutions[pid]
        if not thesis_matches(p):
            raise ValueError('Original prediction does not match frozen thesis: ' + pid)
        if key != opportunity_key(e) or key in seen:
            raise ValueError('Existing opportunity lineage key mismatch')
        seen.add(key)
        expected_hash = e.pop('evidence_hash')
        if digest(e) != expected_hash:
            raise ValueError('Canonical SLOP evidence hash mismatch')
        e['evidence_hash'] = expected_hash
        if any(e[k] != str(getattr(p, k)) for k in ('token_address', 'pair_address', 'frozen_at')):
            raise ValueError('Prediction lineage mismatch')
        if not str(e['token_address']).strip() or not str(e['pair_address']).strip():
            raise ValueError('Missing token/pair identity')
        if not isinstance(e['outcome'], str) or not e['outcome'].strip():
            raise ValueError('Missing resolved outcome label')
        if number(r['friction_bps']) != 200:
            raise ValueError('Resolution friction differs from frozen thesis')
        gross, net = number(e['gross_return']), number(e['net_return'])
        if not math.isclose(net, gross - .02, rel_tol=0, abs_tol=1e-9):
            raise ValueError('Net return does not reconcile with 200 bps friction')
        if timestamp(e['frozen_at']) + timedelta(seconds=60) > captured:
            raise ValueError('Full historical horizon has not elapsed')
        if r.get('execution_authority', False) is not False:
            raise ValueError('Resolution authority mismatch')
        e['opportunity_key'] = key
        e['original_conditions'] = dict(p.conditions)
        rows.append(e)
    rows.sort(key=lambda e: (timestamp(e['frozen_at']), e['prediction_id']))
    body = dict(captured_at=captured_at, rows_json=canonical(rows),
                prediction_ledger_hash=sha256(before[0]).hexdigest(),
                resolution_ledger_hash=sha256(before[1]).hexdigest(), execution_authority=False)
    return EvidenceSnapshot(snapshot_hash=digest(body), **body)
