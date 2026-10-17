"""ORACLE-261: offline exception-code and quote-state evidence; no RPC."""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE258_ROTATION_RAW.json'
OUT = ROOT / 'ORACLE261_EXCEPTION_STATE_EVIDENCE.json'
SAFE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,79}$')
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}


def category(value):
    return value if isinstance(value, str) and SAFE.fullmatch(value) else 'UNSAFE_OR_MISSING_CODE'


def analyze(data):
    if data.get('build') != 'ORACLE241' or any(data.get(k) is not False for k in
            ('signing', 'broadcast', 'execution_admission')):
        raise ValueError('UNTRUSTED_SOURCE')
    observations = data.get('observations')
    if not isinstance(observations, list):
        raise ValueError('OBSERVATIONS_NOT_LIST')
    codes, by_token, call_shapes, timestamps = Counter(), defaultdict(Counter), Counter(), defaultdict(list)
    failures = 0
    for row in observations:
        if not isinstance(row, dict):
            continue
        mint, cycle, size = row.get('mint'), row.get('cycle'), row.get('size_sol')
        if not isinstance(mint, str) or not 32 <= len(mint) <= 44 or type(cycle) is not int:
            continue
        when = row.get('sampled_at')
        if row.get('status') != 'FULL_FILL_GROSS_MEASURED':
            failures += 1
            code = category(row.get('exception_code'))
            codes[code] += 1
            by_token[mint[:12]][code] += 1
            calls = row.get('dlmm_calls')
            call_shapes[type(calls).__name__] += 1
            if isinstance(calls, list):
                call_shapes['length_' + str(min(len(calls), 20))] += 1
                for call in calls[:10]:
                    if isinstance(call, dict):
                        call_shapes['dict_keys_' + ','.join(sorted(str(k) for k in call if SAFE.fullmatch(str(k)))[:8])[:100]] += 1
                        for key in ('error_code','status','reason','code'):
                            if key in call:
                                call_shapes['field_' + key + '_' + category(call[key])] += 1
                    else:
                        call_shapes['item_' + type(call).__name__] += 1
            continue
        quotes = row.get('directions')
        if type(size) not in (int, float) or not isinstance(quotes, list):
            continue
        for q in quotes:
            if not isinstance(q, dict) or q.get('direction') not in DIRECTIONS or type(q.get('gross_lamports')) is not int:
                continue
            key = (mint, round(size, 3), q['direction'])
            timestamps[key].append((cycle, q['gross_lamports'], when if isinstance(when,str) else None))
    repeated, changing, different_times, missing_time = 0, 0, 0, 0
    examples = []
    for (mint, size, direction), rows in timestamps.items():
        if len({c for c, _, _ in rows}) < 2:
            continue
        same = len({gross for _, gross, _ in rows}) == 1
        repeated += int(same)
        changing += int(not same)
        different_times += int(same and len({t for _, _, t in rows if t}) > 1)
        missing_time += int(same and any(not t for _, _, t in rows))
        if len(examples) < 8:
            examples.append({'mint_prefix':mint[:12], 'size_sol':size, 'direction':direction,
                             'same_gross':same, 'different_sample_timestamps':len({t for _,_,t in rows if t})>1,
                             'samples':[{'cycle':c, 'gross':g, 'sampled_at':t} for c,g,t in rows[:4]]})
    return {'build':'ORACLE261','source_observations':len(observations),'failures':failures,
            'exception_codes':dict(codes),'failure_tokens':{k:dict(v) for k,v in sorted(by_token.items())},
            'dlmm_call_shapes':dict(call_shapes),'identical_cross_cycle_keys':repeated,
            'changing_cross_cycle_keys':changing,'identical_with_distinct_sample_timestamps':different_times,
            'identical_with_missing_sample_timestamps':missing_time,'repeat_examples':examples,
            'account_slots_verified':False,'stale_state_proven':False,'net_profit_certified':False,
            'signing':False,'broadcast':False,'execution_admission':False,
            'status':'HOLD_EXCEPTION_CAUSE_AND_ACCOUNT_FRESHNESS'}


def test():
    assert category('DLMM_INSUFFICIENT_BINS') == 'DLMM_INSUFFICIENT_BINS'
    assert category('http://secret') == 'UNSAFE_OR_MISSING_CODE'
    a='A'*32
    source={'build':'ORACLE241','signing':False,'broadcast':False,'execution_admission':False,
            'observations':[{'mint':a,'cycle':1,'status':'HOLD_QUOTE_RuntimeError',
                             'exception_code':'TEST_FAILURE','dlmm_calls':[{'error_code':'TEST_CODE'}]},
                            *[{'mint':a,'cycle':c,'size_sol':.01,'sampled_at':str(c),
                                'status':'FULL_FILL_GROSS_MEASURED',
                                'directions':[{'direction':'PUMP_TO_METEORA','gross_lamports':-123}]} for c in (1,2)]]}
    result=analyze(source)
    assert result['exception_codes']=={'TEST_FAILURE':1}
    assert result['identical_cross_cycle_keys']==1
    assert result['identical_with_distinct_sample_timestamps']==1
    source['signing']=True
    try:analyze(source)
    except ValueError:pass
    else:raise AssertionError('ARMED_SOURCE_ACCEPTED')
    print('[ORACLE261_TEST_PASS] code_counts=TRUE call_shapes=TRUE repeat_timestamps=TRUE fail_closed=TRUE')


def run():
    if not RAW.is_file():raise RuntimeError('ORACLE258_RAW_NOT_FOUND')
    result=analyze(json.loads(RAW.read_text(encoding='utf-8')))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    for key in ('source_observations','failures','exception_codes','dlmm_call_shapes',
                'identical_cross_cycle_keys','changing_cross_cycle_keys',
                'identical_with_distinct_sample_timestamps','status'):
        print('[ORACLE261_'+key.upper()+']',json.dumps(result[key],sort_keys=True))
    for token, values in result['failure_tokens'].items():
        print('[ORACLE261_FAILURE_TOKEN]',json.dumps({'token':token,'codes':values},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()
