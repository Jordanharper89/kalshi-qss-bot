"""ORACLE-259: audit existing 19-size canonical quotes; offline and read-only."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE258_ROTATION_RAW.json'
OUT = ROOT / 'ORACLE259_QUOTE_FAILURE_AND_REUSE.json'
SIZES = tuple(round(.010 + .005 * i, 3) for i in range(19))
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}


def analyze(data):
    if data.get('build') != 'ORACLE241' or any(data.get(k) is not False for k in
        ('signing', 'broadcast', 'execution_admission')):
        raise ValueError('UNTRUSTED_RESEARCH_SOURCE')
    observations = data.get('observations')
    if not isinstance(observations, list):
        raise ValueError('OBSERVATIONS_MISSING')
    stages, by_cycle, repeats = Counter(), defaultdict(Counter), defaultdict(set)
    error_examples, best, token_cycles = {}, [], defaultdict(set)
    for row in observations:
        if not isinstance(row, dict):
            stages['INVALID_OBSERVATION'] += 1
            continue
        cycle, mint, size = row.get('cycle'), row.get('mint'), row.get('size_sol')
        status = str(row.get('status', 'UNKNOWN'))[:70]
        if type(cycle) is not int or not isinstance(mint, str) or not 32 <= len(mint) <= 44 or type(size) not in (int,float) or not any(abs(size-s)<1e-8 for s in SIZES):
            stages['INVALID_IDENTITY_CYCLE_SIZE'] += 1
            continue
        token_cycles[mint].add(cycle)
        by_cycle[cycle][status] += 1
        stages[status] += 1
        if status != 'FULL_FILL_GROSS_MEASURED':
            for name in ('error_code', 'reason', 'error_type'):
                value = row.get(name)
                if isinstance(value, str) and value.isidentifier():
                    error_examples.setdefault(status, set()).add(value[:64])
            continue
        qs, start = row.get('directions'), round(size * 1_000_000_000)
        if (not isinstance(qs, list) or len(qs) != 2 or
            any(not isinstance(q, dict) for q in qs) or
            {q.get('direction') for q in qs} != DIRECTIONS or
            any(type(q.get('start_lamports')) is not int or q['start_lamports'] != start or
                type(q.get('end_lamports')) is not int or q['end_lamports'] <= 0 or
                type(q.get('gross_lamports')) is not int or
                q['gross_lamports'] != q['end_lamports'] - start for q in qs)):
            stages['INVALID_FULL_FILL_ACCOUNTING'] += 1
            continue
        stages['VERIFIED_FULL_FILL_SAMPLES'] += 1
        for q in qs:
            gross = q['gross_lamports']
            key = (mint, round(size,3), q['direction'], gross)
            repeats[key].add(cycle)
            best.append({'token_prefix':mint[:12], 'cycle':cycle, 'size_sol':size,
                         'direction':q['direction'],'gross_lamports':gross,
                         'gross_bps':round(gross*10000/start, 4)})
    repeated = sorted(({'token_prefix':m[:12], 'size_sol':s, 'direction':d,
                        'gross_lamports':g,'cycles':sorted(c)}
                       for (m,s,d,g),c in repeats.items() if len(c) > 1),
                      key=lambda x:(-len(x['cycles']), x['token_prefix']))
    profitable = sorted((x for x in best if x['gross_lamports'] > 0),
                        key=lambda x:x['gross_lamports'], reverse=True)
    cycles = sorted(by_cycle)
    return {'build':'ORACLE259', 'source':'ORACLE258_ROTATION_RAW.json',
            'size_count':len(SIZES), 'min_size_sol':SIZES[0], 'max_size_sol':SIZES[-1],
            'total_observations':len(observations), 'unique_tokens':len(token_cycles),
            'cycles':cycles, 'status_counts':dict(stages),
            'cycle_status_counts':{str(c):dict(by_cycle[c]) for c in cycles},
            'safe_failure_categories':{k:sorted(v) for k,v in error_examples.items()},
            'repeated_identical_quote_keys':len(repeated),
            'identical_quotes_across_cycles_examples':repeated[:15],
            'valid_directions':len(best), 'positive_gross_directions':len(profitable),
            'best_valid_directions':sorted(best,key=lambda x:x['gross_lamports'],reverse=True)[:10],
            'gross_positive_examples':profitable[:10],
            'reuse_is_proven_stale':False, 'state_freshness_certified':False,
            'net_profit_certified':False, 'execution_admission':False,
            'signing':False, 'broadcast':False,
            'status':'REVIEW_POSITIVE_GROSS' if profitable else 'HOLD_NO_POSITIVE_GROSS_DIAGNOSE_QUOTE_FAILURES'}


def test():
    a='A'*32
    def q(direction,end):
        return {'direction':direction,'start_lamports':10_000_000,
                'end_lamports':end,'gross_lamports':end-10_000_000}
    sample={'mint':a,'cycle':1,'size_sol':.01,'status':'FULL_FILL_GROSS_MEASURED',
            'directions':[q('PUMP_TO_METEORA',9_999_900),q('METEORA_TO_PUMP',9_999_800)]}
    src={'build':'ORACLE241','signing':False,'broadcast':False,
         'execution_admission':False,'observations':[sample,dict(sample,cycle=2)]}
    r=analyze(src)
    assert r['repeated_identical_quote_keys']==2 and r['valid_directions']==4
    assert not r['reuse_is_proven_stale'] and r['positive_gross_directions']==0
    sample['directions'][0]['gross_lamports'] = -101
    assert analyze(src)['status_counts']['INVALID_FULL_FILL_ACCOUNTING']==2
    src['signing']=True
    try: analyze(src)
    except ValueError: pass
    else: raise AssertionError('UNSAFE_SOURCE_ACCEPTED')
    print('[ORACLE259_TEST_PASS] sizes=19 accounting=TRUE repeat_detection=TRUE no_execution=TRUE')


def run():
    if not RAW.is_file(): raise RuntimeError('ORACLE258_RAW_REPORT_MISSING')
    result=analyze(json.loads(RAW.read_text(encoding='utf-8')))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE259_RESULT]',json.dumps({k:v for k,v in result.items()
          if k not in ('identical_quotes_across_cycles_examples','best_valid_directions',
                       'gross_positive_examples')},sort_keys=True))
    for row in result['identical_quotes_across_cycles_examples'][:8]:
        print('[ORACLE259_REPEAT]',json.dumps(row,sort_keys=True))
    for row in result['best_valid_directions'][:5]:
        print('[ORACLE259_BEST]',json.dumps(row,sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--run',action='store_true')
    args=ap.parse_args()
    if not args.test and not args.run:ap.error('Specify --test or --run')
    if args.test:test()
    if args.run:run()