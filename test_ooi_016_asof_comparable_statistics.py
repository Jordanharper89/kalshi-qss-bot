import importlib
import tempfile
from dataclasses import replace
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E
S=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_016_asof_comparable_statistics')

def main():
    with tempfile.TemporaryDirectory() as root:
        fixture(root);snap=snapshot(root);op=candidate()
        a=S.comparable_statistics(op,snap);b=S.comparable_statistics(op,snap)
        require(a==b and a['eligible'] and a['case_count']==24,'positive cohort failed')
        require(abs(a['historical_mean_net_return']-.055)<1e-12,'net edge incorrect/double friction')
        require(0<a['historical_positive_net_wilson_lower']<a['positive_net_frequency']<1,'historical statistic invalid')
        require(a['forecast_probability'] is None and not a['calibrated_probability_available'],'forecast falsely claimed')
        future=S.comparable_statistics(candidate(frozen_at='2026-09-16T23:59:59+00:00'),snap)
        require(not future['eligible'] and future['case_count']==0,'future snapshot leaked')
        stale=S.comparable_statistics(candidate(frozen_at='2026-09-17T02:00:00+00:00'),snap)
        require(not stale['eligible'],'stale snapshot admitted')
        self_excluded=S.comparable_statistics(candidate(token_address='token_0'),snap)
        require(self_excluded['case_count']==23,'same-token exclusion failed')
        extra=S.comparable_statistics(candidate(conditions=(('order_flow','BUY_PRESSURE'),('other','X'))),snap)
        require(extra['case_count']==0,'different condition cohort admitted')
        rows=snap.rows();overlap=dict(rows[0]);overlap.update(prediction_id='overlap',opportunity_key='overlap',frozen_at='2026-09-16T23:00:30+00:00')
        rows.append(overlap)
        body=dict(captured_at=snap.captured_at, rows_json=E.canonical(rows), prediction_ledger_hash=snap.prediction_ledger_hash,
            resolution_ledger_hash=snap.resolution_ledger_hash, execution_authority=False)
        overlapped=E.EvidenceSnapshot(snapshot_hash=E.digest(body),**body)
        require(S.comparable_statistics(op,overlapped)['case_count']==24,'overlap inflated sample')
        fixture(root,count=2)
        require(not S.comparable_statistics(op,snapshot(root))['eligible'],'small sample admitted')
        fixture(root,gross=-.05)
        require(not S.comparable_statistics(op,snapshot(root))['eligible'],'negative net edge admitted')
        try:S.comparable_statistics(op,replace(snap,rows_json='[]'))
        except ValueError:pass
        else:raise AssertionError('tampered snapshot accepted')
    print('[PASS] OOI-016 as-of cutoff, condition match, overlap/self exclusion, sample HOLD, friction once')
    print('[POLICY] 20 cases / 3 tokens / 30 days history / snapshot age <= 1 hour')
    print('[SCOPE] descriptive historical statistics; no calibrated forecast; execution_authority=FALSE')

if __name__=='__main__':main()
