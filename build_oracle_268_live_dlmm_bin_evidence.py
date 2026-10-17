"""ORACLE-268: capture live DLMM quote/bin evidence; disarmed, 19 sizes."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE268_DLMM_BIN_EVIDENCE.json')
RAW = OUT.with_name('ORACLE268_CANONICAL_RAW.json')
SIZES = tuple(round(.010 + .005*i, 3) for i in range(19))


def bin_evidence(pool, swap_for_y):
    # No state mutation and no unknown getters invoked.
    result = {'pool_type':type(pool).__name__, 'direction':'X_TO_Y' if swap_for_y else 'Y_TO_X',
              'bin_container':'UNRESOLVED', 'visible_bins':None, 'reserve_positive':None}
    state = vars(pool) if hasattr(pool, '__dict__') else {}
    for key, value in state.items():
        if 'bin' not in key.lower() or key.lower() in ('bin_step','active_id'):
            continue
        if not isinstance(value, (dict,list,tuple)):
            continue
        rows = list(value.values()) if isinstance(value,dict) else list(value)
        if len(rows)>20000: continue
        positive=0
        usable=0
        for b in rows:
            if isinstance(b,dict):
                reserve=b.get('amount_y' if swap_for_y else 'amount_x')
            else:
                reserve=getattr(b, 'amount_y' if swap_for_y else 'amount_x', None)
            if type(reserve) is int:
                usable+=1
                if reserve>0:positive+=1
        if result['visible_bins'] is None or usable>0:
            result.update(bin_container=key, visible_bins=len(rows), reserve_positive=positive,
                          reserve_readable=usable)
        if usable>0: break
    return result


def summarize(rows):
    shapes=Counter()
    for r in rows:
        rem=r.get('remaining_in')
        amount=r.get('amount_in')
        if r.get('error'):
            key='SDK_EXCEPTION_'+r['error']
        elif type(rem) is not int:
            key='NO_REMAINING_IN'
        elif rem==0:
            key='ZERO_REMAINING'
        elif rem==amount:
            key='ENTIRE_INPUT_REMAINING'
        elif 0<rem<amount:
            key='PARTIAL_INPUT_REMAINING'
        else:
            key='INCONSISTENT_REMAINING'
        shapes[key]+=1
    return dict(shapes)


def test():
    class Bin:
        amount_x=0
        amount_y=42
    class Pool:
        def __init__(self):self.bins=[Bin(),Bin()]
    e=bin_evidence(Pool(),True)
    assert e['visible_bins']==2 and e['reserve_positive']==2
    assert bin_evidence(Pool(),False)['reserve_positive']==0
    assert summarize([{'amount_in':10,'remaining_in':10},{'amount_in':10,'remaining_in':0}])=={
        'ENTIRE_INPUT_REMAINING':1,'ZERO_REMAINING':1}
    assert len(SIZES)==19 and SIZES[0]==.010 and SIZES[-1]==.100
    print('[ORACLE268_TEST_PASS] size_grid=19 bin_reserves=TRUE remaining=TRUE disarmed=TRUE')


def run():
    if os.getenv('QSB_LIVE_ARM','NO').upper()!='NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_ENV_REQUIRED')
    if not os.getenv('SOLANA_RPC_URL','').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    import meteora_dlmm
    import build_oracle_241_live_opportunity_sampler as sampler
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
    original, prior_sizes, prior_out = meteora_dlmm.quote, sampler.SIZES, sampler.OUT
    g=pd.prepare_pairs.__globals__
    cap=g.get('MAX_PAIRS')
    if type(cap) is not int or cap<1:raise RuntimeError('UNVERIFIED_PAIR_CAP')
    observations=[]
    def capture(pool, amount_in, swap_for_y, *args, **kwargs):
        if len(observations)>=2000:raise RuntimeError('QUOTE_TRACE_CAP')
        row={'amount_in':int(amount_in), **bin_evidence(pool,swap_for_y)}
        observations.append(row)
        try:
            q=original(pool,amount_in,swap_for_y,*args,**kwargs)
            rem=getattr(q,'remaining_in',None)
            row.update(remaining_in=rem if type(rem) is int else None,
                       complete=getattr(q,'complete',None) is True,
                       amount_out=int(getattr(q,'amount_out',0)))
            return q
        except Exception as e:
            row['error']=type(e).__name__
            raise
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if RAW.exists(): RAW.unlink()
    try:
        meteora_dlmm.quote=capture
        sampler.SIZES, sampler.OUT=SIZES,RAW
        g['MAX_PAIRS']=max(cap,12)
        sampler.run(1,12,0)
    finally:
        meteora_dlmm.quote=original
        sampler.SIZES,sampler.OUT=prior_sizes,prior_out
        g['MAX_PAIRS']=cap
    if not RAW.exists():raise RuntimeError('CANONICAL_REPORT_MISSING')
    raw=json.loads(RAW.read_text(encoding='utf-8'))
    if raw.get('build')!='ORACLE241' or any(raw.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_CANONICAL_RESULT')
    result={'build':'ORACLE268','sizes_sol':list(SIZES),'canonical_observations':len(raw.get('observations',[])),
            'sdk_quote_calls':len(observations),'quote_categories':summarize(observations),
            'bin_container_counts':dict(Counter(str(x['bin_container']) for x in observations)),
            'zero_visible_reserve_quotes':sum(x.get('reserve_positive')==0 for x in observations),
            'unknown_visible_reserve_quotes':sum(x.get('reserve_positive') is None for x in observations),
            'examples':observations[:30], 'scanner_changed':False,'signing':False,'broadcast':False,
            'net_profit_certified':False,'execution_admission':False,
            'status':'HOLD_BIN_EVIDENCE_REQUIRES_FRESH_NET_ATOMIC'}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE268_RESULT]',json.dumps({k:v for k,v in result.items() if k not in ('examples','sizes_sol')},sort_keys=True))
    for row in observations[:8]:print('[ORACLE268_BIN]',json.dumps(row,sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()
