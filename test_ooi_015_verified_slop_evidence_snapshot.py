import copy
import importlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

E = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_015_verified_slop_evidence_snapshot')
P = importlib.import_module('qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze').ProspectiveOpportunity
FIXED = '2026-09-17T00:00:00+00:00'
CANDIDATE_TIME = '2026-09-17T00:00:10+00:00'

def require(value, message):
    if not value:
        raise AssertionError(message)

def fixture(root, count=24, gross=.10):
    predictions, resolutions = [], []
    for i in range(count):
        pid = 'historical_' + str(i)
        value = gross if i < 20 else -.05
        predictions.append(dict(prediction_id=pid, token_address='token_'+str(i), pair_address='pair_'+str(i),
            frozen_at='2026-09-16T23:00:00+00:00', conditions=[['order_flow','BUY_PRESSURE']],
            horizon_seconds=60, target=.10, stop=.05, friction_bps=200,
            state='PENDING_60S', execution_authority=False))
        resolutions.append(dict(prediction_id=pid, outcome='TARGET_FIRST' if value>0 else 'STOP_FIRST',
            gross_return=value, net_return=value-.02, terminal_return=value,
            mfe=max(value,0), mae=min(value,0), friction_bps=200, execution_authority=False))
    for relative, key, values in [(E.PREDICTIONS,'predictions',predictions),(E.RESOLUTIONS,'resolutions',resolutions)]:
        path=Path(root)/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({key:values}),encoding='utf-8')
    return predictions, resolutions

def snapshot(root):
    with patch.object(E,'utc_now',return_value=FIXED):
        return E.read_evidence_snapshot(root)

def candidate(**changes):
    values=dict(prediction_id='candidate', token_address='new_token', pair_address='new_pair',
        frozen_at=CANDIDATE_TIME, conditions=(('order_flow','BUY_PRESSURE'),),
        horizon_seconds=60, target=.10, stop=.05, friction_bps=200)
    values.update(changes)
    return P(**values)

def main():
    with tempfile.TemporaryDirectory() as root:
        ps, rs=fixture(root)
        paths=[Path(root)/E.PREDICTIONS,Path(root)/E.RESOLUTIONS]
        before=[p.read_bytes() for p in paths]
        a=snapshot(root);b=snapshot(root)
        require(a==b and len(a.rows())==24,'snapshot replay/count failed')
        require([p.read_bytes() for p in paths]==before,'reader modified existing ledgers')
        require(a.rows()[0]['original_conditions']=={'order_flow':'BUY_PRESSURE'},'original thesis not retained')
        ps[0]['target']=.20
        paths[0].write_text(json.dumps({'predictions':ps}))
        try:snapshot(root)
        except ValueError:pass
        else:raise AssertionError('hardcoded upstream thesis masked original mismatch')
        fixture(root)
        ps,rs=fixture(root);rs[0]['net_return']=.10
        paths[1].write_text(json.dumps({'resolutions':rs}))
        try:snapshot(root)
        except ValueError:pass
        else:raise AssertionError('friction mismatch accepted')
        ps,rs=fixture(root);ps.append(copy.deepcopy(ps[0]))
        paths[0].write_text(json.dumps({'predictions':ps}))
        try:snapshot(root)
        except ValueError:pass
        else:raise AssertionError('duplicate ledger id accepted')
    print('[PASS] OOI-015 actual SLOP readers, hash/lineage validation, original thesis check, no ledger writes')
    print('[SCOPE] Temporary deterministic fixtures; execution_authority=FALSE')

if __name__=='__main__':main()
