"""ORACLE-258 full 19-size rotating Mriya and canonical opportunity watch; read-only."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE258_ROTATION_RAW.json'
OUT = ROOT / 'ORACLE258_ROTATION_WATCH.json'
SIZES = tuple(round(.010 + i * .005, 3) for i in range(19))
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}


def evaluate(source, observed):
    if source.get('build') != 'ORACLE241' or any(source.get(k) is not False for k in ('signing', 'broadcast', 'execution_admission')):
        raise ValueError('UNTRUSTED_CANONICAL_REPORT')
    records, holds, unique = [], Counter(), set()
    for s in source.get('observations', []):
        if not isinstance(s, dict):
            holds['INVALID_SAMPLE'] += 1
            continue
        mint, size = s.get('mint'), s.get('size_sol')
        if not isinstance(mint, str) or type(size) not in (int, float) or not any(abs(size-x)<1e-9 for x in SIZES):
            holds['INVALID_IDENTITY_OR_SIZE'] += 1
            continue
        unique.add(mint)
        if s.get('status') != 'FULL_FILL_GROSS_MEASURED':
            holds[str(s.get('status', 'UNKNOWN'))[:64]] += 1
            continue
        qs = s.get('directions')
        start = round(size * 1_000_000_000)
        if (not isinstance(qs, list) or len(qs) != 2 or any(not isinstance(q, dict) for q in qs)
            or {q.get('direction') for q in qs} != DIRECTIONS
            or any(type(q.get('start_lamports')) is not int or q['start_lamports'] != start
                   or type(q.get('end_lamports')) is not int or q['end_lamports'] <= 0
                   or type(q.get('gross_lamports')) is not int or q['gross_lamports'] != q['end_lamports'] - start for q in qs)):
            holds['INVALID_FULL_FILL_ACCOUNTING'] += 1
            continue
        for q in qs:
            records.append({'token': mint, 'cycle': s.get('cycle'), 'size_sol': round(size,3),
                            'direction': q['direction'], 'gross_lamports': q['gross_lamports'],
                            'gross_bps': round(q['gross_lamports'] * 10000 / start, 4),
                            'mriya_seen_in_window': mint in observed})
    positives = sorted((r for r in records if r['gross_lamports'] > 0), key=lambda x: x['gross_lamports'], reverse=True)
    best = sorted(records, key=lambda x:x['gross_lamports'], reverse=True)
    return {'build':'ORACLE258', 'sizes_sol':list(SIZES), 'mriya_unique_tokens':len(observed),
            'priced_unique_tokens':len(unique), 'attempts':len(source.get('observations', [])),
            'valid_full_fill_samples':len(records)//2, 'valid_directions':len(records),
            'positive_gross_directions':len(positives),
            'positive_mriya_directions':sum(r['mriya_seen_in_window'] for r in positives),
            'positive_candidates':positives[:20], 'top_gross':best[:10], 'quote_holds':dict(holds),
            'net_profit_certified':False, 'state_freshness_certified':False,
            'atomic_simulation_certified':False, 'signing':False, 'broadcast':False,
            'execution_admission':False, 'status':'RESEARCH_POSITIVE_GROSS_REQUIRES_NET_ATOMIC' if positives else 'HOLD_NO_POSITIVE_GROSS'}


def test():
    assert len(SIZES)==19 and SIZES[0]==.010 and SIZES[-1]==.100 and SIZES[1]==.015
    a = 'A'*32
    def quote(d,end):
        return {'direction':d, 'start_lamports':10_000_000, 'end_lamports':end, 'gross_lamports':end-10_000_000}
    s={'build':'ORACLE241','signing':False,'broadcast':False,'execution_admission':False,
       'observations':[{'mint':a,'size_sol':.01,'status':'FULL_FILL_GROSS_MEASURED',
                        'directions':[quote('PUMP_TO_METEORA',10_001_000),quote('METEORA_TO_PUMP',9_999_000)]}]}
    r=evaluate(s,{a})
    assert r['positive_mriya_directions']==1 and r['valid_full_fill_samples']==1
    s['observations'][0]['directions'][0]['gross_lamports']=999
    assert evaluate(s,{a})['valid_directions']==0
    s['signing']=True
    try: evaluate(s,{a})
    except ValueError: pass
    else: raise AssertionError('ARMED_SOURCE_ACCEPTED')
    print('[ORACLE258_TEST_PASS] sizes=19 min=0.010 max=0.100 accounting=TRUE execution=FALSE')


def run(cycles,gap):
    if os.getenv('QSB_LIVE_ARM','NO').upper()!='NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_ENV_REQUIRED')
    if not os.getenv('SOLANA_RPC_URL','').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    import build_oracle_241_live_opportunity_sampler as sampler
    import build_oracle_257_mriya_pricing_gate as prior
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine, live_account_stream as pd
    g=pd.prepare_pairs.__globals__
    cap=g.get('MAX_PAIRS')
    if type(cap) is not int or not 1<=cap<=100: raise RuntimeError('UNVERIFIED_CAP')
    old_fn,old_sizes,old_out=engine.mriya_hot_tokens,sampler.SIZES,sampler.OUT
    seen, calls=set(), []
    def watch(*args,**kw):
        items=old_fn(*args,**kw)
        if not isinstance(items,(tuple,list)):raise RuntimeError('BAD_MRIYA_RETURN')
        found=prior.tokens(items)
        seen.update(found)
        calls.append(len(found))
        return items
    ROOT.mkdir(parents=True,exist_ok=True)
    if RAW.exists(): RAW.unlink()
    try:
        g['MAX_PAIRS']=max(cap,12)
        engine.mriya_hot_tokens=watch
        sampler.SIZES,sampler.OUT=SIZES,RAW
        sampler.run(cycles,12,gap)
    finally:
        g['MAX_PAIRS']=cap
        engine.mriya_hot_tokens=old_fn
        sampler.SIZES,sampler.OUT=old_sizes,old_out
    if not RAW.is_file(): raise RuntimeError('CANONICAL_REPORT_MISSING')
    result=evaluate(json.loads(RAW.read_text(encoding='utf-8')),seen)
    result['mriya_calls']=calls
    result['original_pair_cap_restored']=g['MAX_PAIRS']==cap
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE258_RESULT]',json.dumps({k:v for k,v in result.items() if k not in ('positive_candidates','top_gross','sizes_sol')},sort_keys=True))
    for tag, rows in (('POSITIVE_GROSS',result['positive_candidates']),('TOP_GROSS',result['top_gross'][:5])):
        for x in rows:print('[ORACLE258_'+tag+']',json.dumps({**x,'token':x['token'][:12]},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--cycles',type=int,default=3);p.add_argument('--gap',type=int,default=20)
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(1,min(a.cycles,5)),max(15,min(a.gap,60)))
