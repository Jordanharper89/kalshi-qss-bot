import importlib
import json
import sys
from pathlib import Path
from test_ooi_015_verified_slop_evidence_snapshot import require
L=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_023_bounded_live_observation_gate')

def fixture_checks():
    empty=dict(decisions=[],active_owned_count=0,read_only=True,execution_authority=False)
    held=L.summarize_observation([empty])
    require(not held['live_nonempty_certified'] and held['status']=='HOLD_NO_LIVE_ADMISSION','empty stream passed live gate')
    accepted=dict(empty,decisions=[dict(prediction_id='fixture-only',status='RESEARCH_ACCEPTED',reasons=[])],active_owned_count=1)
    report=L.summarize_observation([accepted,accepted])
    require(report['unique_accepted_count']==1 and report['cycle_count']==2,'duplicate observation inflated admission')
    require(report['continuous_runtime_activation_certified'] is False,'bounded gate claimed continuous runtime')
    try:L.summarize_observation([dict(empty,execution_authority=True)])
    except ValueError:pass
    else:raise AssertionError('execution authority breach accepted')
    print('[PASS] OOI-023 live-gate accounting tests; empty stream remains HOLD')

def physical_check():
    print('[OBSERVE] Up to 90 seconds. Existing Oracle producer must supply fresh predictions; no producer is started here.',flush=True)
    result=L.run_live_gate(Path(__file__).resolve().parent,duration_seconds=90)
    print('[LIVE_RESULT]',json.dumps(result,sort_keys=True),flush=True)
    if result['live_nonempty_certified']:
        print('[PASS] NONEMPTY LIVE RESEARCH HANDOFF OBSERVED; execution_authority=FALSE',flush=True)
    else:
        print('[HOLD] No qualifying live handoff observed. Live nonempty certification remains pending.',flush=True)
    print('[SCOPE] Bounded observation only; 24/7 activation is not certified.',flush=True)

if __name__=='__main__':
    fixture_checks()
    if '--fixture-only' not in sys.argv:physical_check()
