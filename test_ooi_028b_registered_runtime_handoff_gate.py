import importlib
import json
import sys
R=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_028_registered_runtime_handoff_gate')

def main():
    now='2026-09-17T00:00:30+00:00'
    base=dict(revision='OOI_026',child='run_slop_buy_pressure_live.py',pid=123,
        updated_at=now,state='PRODUCER_AND_OBSERVER_HEALTHY',round_count=1,
        read_only=True,execution_authority=False,
        observation=dict(read_only=True,execution_authority=False,decisions=[]))
    assert not R.summarize([],now)['live_nonempty_certified']
    assert not R.summarize([base],now)['producer_round_progress_observed']
    advanced=dict(base,round_count=2)
    held=R.summarize([base,advanced],now)
    assert held['producer_round_progress_observed'] and not held['live_nonempty_certified']
    decision=dict(status='RESEARCH_ACCEPTED',prediction_id='fixture-only',
        snapshot_captured_at='2026-09-17T00:00:00+00:00',frozen_at='2026-09-17T00:00:10+00:00')
    advanced=dict(advanced,observation=dict(read_only=True,execution_authority=False,decisions=[decision]))
    assert R.summarize([base,advanced],now)['live_nonempty_certified']
    stale=dict(base,updated_at='2026-09-16T00:00:00+00:00')
    assert not R.summarize([stale],now)['live_nonempty_certified']
    try:R.summarize([dict(base,execution_authority=True)],now)
    except ValueError:pass
    else:raise AssertionError('Authority violation ignored')
    print('[PASS] OOI-028 deterministic fresh/stale, progression, nonempty and authority gates')
    if '--live' in sys.argv:
        result=R.run_gate(duration_seconds=30)
        print('[LIVE_RESULT] '+json.dumps(result,sort_keys=True))
        if not result['live_nonempty_certified']:print('[HOLD] Return the JSON report; no admission bypass')
        print('[SCOPE] Bounded runtime observation; 24/7 activation remains uncertified')

if __name__=='__main__':main()
