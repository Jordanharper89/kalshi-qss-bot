"""ORACLE-250: coarse-size live opportunity screening; strictly research-only."""
import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE250_COARSE_RAW.json'
OUT = ROOT / 'ORACLE250_OPPORTUNITY_SCREEN.json'
SIZES = (0.010, 0.030, 0.060, 0.100)
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}


def evaluate(source):
    if not isinstance(source, dict) or any(source.get(k) is not False for k in
        ('signing', 'broadcast', 'execution_admission')) or source.get('build') != 'ORACLE241':
        raise ValueError('UNTRUSTED_SOURCE')
    totals = Counter()
    by_mint = defaultdict(lambda: {'samples': 0, 'positive': [], 'best': None, 'holds': Counter()})
    for sample in source.get('observations', []):
        if not isinstance(sample, dict):
            totals['BAD_SAMPLE'] += 1
            continue
        mint, size = sample.get('mint'), sample.get('size_sol')
        if not isinstance(mint, str) or len(mint) < 32 or type(size) not in (int, float) or not any(abs(size-x)<1e-9 for x in SIZES):
            totals['BAD_IDENTITY_OR_SIZE'] += 1
            continue
        item = by_mint[mint]
        item['samples'] += 1
        if sample.get('status') != 'FULL_FILL_GROSS_MEASURED':
            name = str(sample.get('status', 'UNKNOWN'))[:70]
            totals[name] += 1
            item['holds'][name] += 1
            continue
        quotes = sample.get('directions')
        start = round(size*1_000_000_000)
        if not isinstance(quotes, list) or len(quotes) != 2 or any(not isinstance(q, dict) for q in quotes) or {q.get('direction') for q in quotes} != DIRECTIONS or any(type(q.get('start_lamports')) is not int or q['start_lamports'] != start or type(q.get('end_lamports')) is not int or q['end_lamports'] <= 0 or type(q.get('gross_lamports')) is not int or q['gross_lamports'] != q['end_lamports']-start for q in quotes):
            totals['BAD_QUOTE_ACCOUNTING'] += 1
            item['holds']['BAD_QUOTE_ACCOUNTING'] += 1
            continue
        totals['FULL_FILL_SAMPLES'] += 1
        for q in quotes:
            record = {'mint': mint, 'cycle': sample.get('cycle'), 'size_sol': round(size, 3),
                      'direction': q['direction'], 'gross_lamports': q['gross_lamports'],
                      'gross_bps': round(q['gross_lamports']*10000/start, 4)}
            if item['best'] is None or record['gross_lamports'] > item['best']['gross_lamports']:
                item['best'] = record
            if q['gross_lamports'] > 0:
                item['positive'].append(record)
                totals['POSITIVE_DIRECTION_SAMPLES'] += 1
    rows = []
    for mint, item in by_mint.items():
        positive = sorted(item['positive'], key=lambda x:x['gross_lamports'], reverse=True)
        rows.append({'mint': mint, 'token_prefix': mint[:12], 'samples': item['samples'],
                     'best_observed': item['best'], 'positive_count': len(positive),
                     'positive_examples': positive[:5], 'holds': dict(item['holds']),
                     'decision': 'RECHECK_WITH_FINE_SIZING' if positive else 'NO_POSITIVE_COARSE_QUOTE',
                     'execution_admission': False})
    rows.sort(key=lambda r: (r['positive_count'] > 0,
                             r['best_observed']['gross_lamports'] if r['best_observed'] else -10**18), reverse=True)
    return rows, dict(totals)


def test():
    def q(direction, end):
        return {'direction':direction, 'start_lamports':10_000_000,
                'end_lamports':end, 'gross_lamports':end-10_000_000}
    source = {'build':'ORACLE241','signing':False,'broadcast':False,'execution_admission':False,
              'observations':[{'mint':'A'*44,'size_sol':.01,'status':'FULL_FILL_GROSS_MEASURED',
                               'directions':[q('PUMP_TO_METEORA',10_001_000),q('METEORA_TO_PUMP',9_999_000)]}]}
    rows, count = evaluate(source)
    assert len(rows)==1 and rows[0]['positive_count']==1 and count['POSITIVE_DIRECTION_SAMPLES']==1
    source['observations'][0]['directions'][0]['gross_lamports']=900
    rows, count = evaluate(source)
    assert rows[0]['best_observed'] is None and count['BAD_QUOTE_ACCOUNTING']==1
    source['signing']=True
    try: evaluate(source)
    except ValueError: pass
    else: raise AssertionError('unsafe source accepted')
    print('[ORACLE250_TEST_PASS] coarse_sizes=4 positive_filter=TRUE accounting=TRUE execution=FALSE')


def run(cycles, pairs, gap):
    if os.environ.get('QSB_LIVE_ARM','NO').upper() != 'NO' or os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_ENV_REQUIRED')
    if not os.environ.get('SOLANA_RPC_URL','').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    import build_oracle_241_live_opportunity_sampler as sampler
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
    g = pd.prepare_pairs.__globals__
    prior_cap = g.get('MAX_PAIRS')
    if type(prior_cap) is not int or not 1 <= prior_cap <= 100:
        raise RuntimeError('UNVERIFIED_PAIR_CAP')
    before_sizes, before_out = sampler.SIZES, sampler.OUT
    ROOT.mkdir(parents=True, exist_ok=True)
    if RAW.exists(): RAW.unlink()
    try:
        g['MAX_PAIRS'] = max(prior_cap, pairs)
        sampler.SIZES, sampler.OUT = SIZES, RAW
        sampler.run(cycles, pairs, gap)
    finally:
        g['MAX_PAIRS'] = prior_cap
        sampler.SIZES, sampler.OUT = before_sizes, before_out
    if not RAW.is_file():
        raise RuntimeError('MISSING_LIVE_REPORT')
    raw = json.loads(RAW.read_text(encoding='utf-8'))
    rows, counts = evaluate(raw)
    result = {'build':'ORACLE250', 'sizes_sol':SIZES, 'cycles':len(raw.get('cycles',[])),
              'samples':len(raw.get('observations',[])), 'unique_tokens':len(rows),
              'positive_tokens':sum(r['positive_count']>0 for r in rows), 'counts':counts,
              'top_routes':rows, 'cap_restored':g['MAX_PAIRS']==prior_cap,
              'security_certified':False, 'fresh_state_certified':False, 'net_profit_certified':False,
              'signing':False, 'broadcast':False, 'execution_admission':False,
              'status':'RESEARCH_ONLY_NO_TRADE_AUTHORITY'}
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE250_RESULT]',json.dumps({k:v for k,v in result.items() if k!='top_routes'},sort_keys=True))
    for row in rows:
        print('[ORACLE250_ROUTE]', json.dumps({'token':row['token_prefix'], 'samples':row['samples'],
            'positive_count':row['positive_count'], 'best':row['best_observed'],
            'holds':row['holds'], 'decision':row['decision']},sort_keys=True))
    print('[REPORT]',OUT)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true'); p.add_argument('--run',action='store_true')
    p.add_argument('--cycles',type=int,default=3);p.add_argument('--pairs',type=int,default=12)
    p.add_argument('--gap',type=int,default=15)
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(1,min(a.cycles,5)),max(4,min(a.pairs,20)),max(10,min(a.gap,60)))