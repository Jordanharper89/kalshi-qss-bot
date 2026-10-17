"""ORACLE-254: single-run Mriya-to-canonical-quote research; no trades."""
import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE254_CANONICAL_RAW.json'
OUT = ROOT / 'ORACLE254_MRIYA_QUOTE_HANDOFF.json'
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SIZES = (0.010, 0.030)


def ids(obj):
    """Collect public mint identities from expected Mriya row shapes."""
    result = set()
    if isinstance(obj, (list, tuple, set)):
        for item in list(obj)[:200]:
            result.update(ids(item))
    elif isinstance(obj, dict):
        for key in ('token', 'mint', 'token_mint', 'base_mint'):
            value = obj.get(key)
            if isinstance(value, str) and B58.fullmatch(value):
                result.add(value)
    elif isinstance(obj, str) and B58.fullmatch(obj):
        result.add(obj)
    return result


def evaluate(source, hot, raw, exact):
    if (source.get('build') != 'ORACLE241' or
        any(source.get(k) is not False for k in
            ('signing', 'broadcast', 'execution_admission'))):
        raise ValueError('UNTRUSTED_QUOTE_REPORT')
    by_mint = {}
    for entry in source.get('observations', []):
        if not isinstance(entry, dict):
            continue
        mint = entry.get('mint')
        if not isinstance(mint, str) or not B58.fullmatch(mint):
            continue
        item = by_mint.setdefault(mint, {'attempts': 0, 'valid_samples': 0,
                                          'holds': Counter(), 'best_gross': None})
        item['attempts'] += 1
        if entry.get('status') != 'FULL_FILL_GROSS_MEASURED':
            item['holds'][str(entry.get('status', 'UNKNOWN'))[:75]] += 1
            continue
        size = entry.get('size_sol')
        if type(size) not in (int, float) or not any(abs(size-s)<1e-9 for s in SIZES):
            item['holds']['INVALID_SIZE'] += 1
            continue
        qs = entry.get('directions')
        start = round(size * 1_000_000_000)
        if (not isinstance(qs, list) or len(qs) != 2 or
            {q.get('direction') for q in qs if isinstance(q, dict)} !=
                {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'} or
            any(not isinstance(q, dict) or
                type(q.get('start_lamports')) is not int or q['start_lamports'] != start or
                type(q.get('end_lamports')) is not int or q['end_lamports'] <= 0 or
                type(q.get('gross_lamports')) is not int or
                q['gross_lamports'] != q['end_lamports'] - start for q in qs)):
            item['holds']['ACCOUNTING_HOLD'] += 1
            continue
        item['valid_samples'] += 1
        best = max(q['gross_lamports'] for q in qs)
        if item['best_gross'] is None or best > item['best_gross']:
            item['best_gross'] = best
    universe = sorted(set(hot) | set(raw) | set(exact))
    rows = []
    for mint in universe:
        v = by_mint.get(mint, {})
        gross = v.get('best_gross')
        rows.append({'mint': mint, 'mriya': mint in hot,
                     'raw': mint in raw, 'exact': mint in exact,
                     'quoted': bool(v.get('valid_samples', 0)),
                     'attempts': v.get('attempts', 0),
                     'best_gross_lamports': gross,
                     'positive_gross': gross is not None and gross > 0,
                     'holds': dict(v.get('holds', {}))})
    return rows


def test():
    a, b = 'A'*32, 'B'*32
    assert ids([{'token': a}, {'mint': b}]) == {a, b}
    assert not ids([{'private_key': a, 'pool': b}])
    src = {'build':'ORACLE241','signing':False,'broadcast':False,
           'execution_admission':False,'observations':[
               {'mint':a,'status':'FULL_FILL_GROSS_MEASURED','size_sol':.01,
                'directions':[{'direction':d,'start_lamports':10_000_000,
                               'end_lamports':10_001_000,'gross_lamports':1000}
                              for d in ('PUMP_TO_METEORA','METEORA_TO_PUMP')]}]}
    rows = evaluate(src, {a,b}, {a}, {a})
    assert rows[0]['positive_gross'] and rows[0]['quoted']
    assert not rows[1]['quoted']
    src['observations'][0]['directions'][0]['gross_lamports'] = 900
    assert not evaluate(src, {a}, {a}, {a})[0]['quoted']
    print('[ORACLE254_TEST_PASS] provenance=TRUE quote_accounting=TRUE fail_closed=TRUE')


def run():
    if os.environ.get('QSB_LIVE_ARM', 'NO').upper() != 'NO' or os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_ENV_REQUIRED')
    if not os.environ.get('SOLANA_RPC_URL','').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    import build_oracle_241_live_opportunity_sampler as sampler
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine, live_account_stream as pd
    g = pd.prepare_pairs.__globals__
    cap = g.get('MAX_PAIRS')
    if type(cap) is not int or not 1 <= cap <= 100:
        raise RuntimeError('CAP_UNVERIFIED')
    saved = (engine.mriya_hot_tokens, engine.raw_candidate_universe,
             engine.candidate_universe, sampler.SIZES, sampler.OUT)
    seen = {'hot': set(), 'raw': set(), 'exact': set()}
    calls = Counter()
    def watch(name, fn):
        def wrapper(*a, **kw):
            result = fn(*a, **kw)
            calls[name] += 1
            seen[name].update(ids(result))
            return result
        return wrapper
    ROOT.mkdir(parents=True, exist_ok=True)
    if RAW.exists():
        RAW.unlink()
    try:
        g['MAX_PAIRS'] = max(cap, 12)
        engine.mriya_hot_tokens = watch('hot', saved[0])
        engine.raw_candidate_universe = watch('raw', saved[1])
        engine.candidate_universe = watch('exact', saved[2])
        sampler.SIZES, sampler.OUT = SIZES, RAW
        sampler.run(1, 12, 0)
    finally:
        g['MAX_PAIRS'] = cap
        (engine.mriya_hot_tokens, engine.raw_candidate_universe,
         engine.candidate_universe, sampler.SIZES, sampler.OUT) = saved
    if not RAW.is_file():
        raise RuntimeError('SAMPLER_REPORT_MISSING')
    data = json.loads(RAW.read_text(encoding='utf-8'))
    rows = evaluate(data, seen['hot'], seen['raw'], seen['exact'])
    mriya = [r for r in rows if r['mriya']]
    result = {'build':'ORACLE254','function_invocations':dict(calls),
              'mriya_count':len(mriya), 'mriya_raw':sum(r['raw'] for r in mriya),
              'mriya_exact':sum(r['exact'] for r in mriya),
              'mriya_quoted':sum(r['quoted'] for r in mriya),
              'mriya_positive_gross':sum(r['positive_gross'] for r in mriya),
              'quoted_total':sum(r['quoted'] for r in rows),
              'mriya_rows':mriya, 'cap_restored':g['MAX_PAIRS']==cap,
              'current_event_freshness_certified':False,'net_profit_certified':False,
              'execution_admission':False,'signing':False,'broadcast':False,
              'status':'HOLD_FRESHNESS_NET_AND_ATOMIC_CERTIFICATION'}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE254_RESULT]',json.dumps({k:v for k,v in result.items() if k != 'mriya_rows'},sort_keys=True))
    for row in mriya:
        print('[ORACLE254_MRIYA]',json.dumps({**row,'mint':row['mint'][:12]},sort_keys=True))
    print('[REPORT]',OUT)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not a.test and not a.run:p.error('use --test or --run')
    if a.test:test()
    if a.run:run()