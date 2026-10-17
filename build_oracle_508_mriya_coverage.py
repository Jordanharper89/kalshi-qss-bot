
from pathlib import Path
import ast

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_508_mriya_coverage.py')
SOURCE = r'''from __future__ import annotations
import argparse, json, os, re, time, urllib.error
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

ROOT=Path('runtime_state/oracle/oracle_live_execution')
STATE=ROOT/'oracle_508_mriya_coverage.json'
CHECKPOINT=ROOT/'oracle_508_mriya_cursor.json'
TOKENS=ROOT/'oracle_508_mriya_tokens.json'
TX_CONFIG={'encoding':'jsonParsed','commitment':'confirmed','maxSupportedTransactionVersion':1}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    try:
        tmp.write_text(json.dumps(value, sort_keys=True, indent=2), encoding='utf-8')
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()


def read_json(path, default):
    if not path.exists(): return default
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict): raise ValueError('INVALID_STATE_JSON')
    return data


def rpc_call(rpc, method, params):
    for attempt in range(3):
        try: return rpc(method,params)
        except (RuntimeError,urllib.error.HTTPError) as exc:
            msg=str(exc)
            limited=getattr(exc,'code',None)==429 or '429' in msg or '-32005' in msg
            if not limited or attempt==2: raise
            time.sleep(0.6 * (2**attempt))


def page_walk(rpc, anchor, size=16, pages=4):
    if not 1<=size<=1000 or not 1<=pages<=20: raise ValueError('INVALID_BOUNDS')
    found=[]; seen=set(); before=None; exhausted=False
    for _ in range(pages):
        opts={'limit':size,'commitment':'confirmed'}
        if anchor: opts['until']=anchor
        if before: opts['before']=before
        page=rpc_call(rpc,'getSignaturesForAddress',[engine.MRIYA,opts])
        if not isinstance(page,list): raise RuntimeError('BAD_SIGNATURE_PAGE')
        if not page: exhausted=True; break
        for row in page:
            sig=row.get('signature') if isinstance(row,dict) else None
            if not isinstance(sig,str) or not sig: raise RuntimeError('BAD_SIGNATURE')
            if sig==anchor: exhausted=True; break
            if sig in seen: raise RuntimeError('PAGINATION_DUPLICATE')
            seen.add(sig); found.append(row)
        if exhausted or len(page)<size: exhausted=True; break
        tail=page[-1]['signature']
        if tail==before: raise RuntimeError('PAGINATION_STALLED')
        before=tail
    return found,exhausted


def backfill_page(rpc, before, size=16):
    if not before: return [],True
    rows=rpc_call(rpc,'getSignaturesForAddress',[engine.MRIYA,{
        'limit':size,'before':before,'commitment':'confirmed'}])
    if not isinstance(rows,list): raise RuntimeError('BAD_BACKFILL_PAGE')
    if len({r.get('signature') for r in rows if isinstance(r,dict)})!=len(rows):
        raise RuntimeError('BAD_BACKFILL_SIGNATURES')
    return rows,len(rows)<size


def fetch_tokens(rpc, signatures, sleep_s=0.20):
    found={}; failed=0
    for row in signatures:
        if row.get('err') is not None:
            failed+=1; continue
        if sleep_s: time.sleep(sleep_s)
        tx=rpc_call(rpc,'getTransaction',[row['signature'],dict(TX_CONFIG)])
        if not isinstance(tx,dict): raise RuntimeError('TRANSACTION_MISSING')
        ver=tx.get('version','legacy')
        if ver not in ('legacy',0,1): raise RuntimeError('TRANSACTION_VERSION_UNEXPECTED')
        for token in engine._tx_mints(tx):
            if not isinstance(token,str) or len(token)<32: continue
            found[token]={'token':token,'source':'MRIYA_COVERAGE',
                          'signature':row['signature'],'observed_unix':time.time()}
    return found,failed


def capture(rpc, checkpoint, size=16, pages=4, sleep_s=0.20):
    head=checkpoint.get('head') or checkpoint.get('newest')
    first=not bool(head)
    if first:
        new,full=page_walk(rpc,None,size,1)
    else:
        new,full=page_walk(rpc,head,size,pages)
    if not full and not first:
        raise RuntimeError('INCREMENTAL_GAP_PAGE_LIMIT')
    next_head=new[0]['signature'] if new else head
    back_before=checkpoint.get('backfill_before')
    if checkpoint.get('newest') and not checkpoint.get('head') and not back_before:
        back_before=head
    history_done=bool(checkpoint.get('history_complete',False))
    if first:
        back_before=new[-1]['signature'] if new and not full else None
        history_done=full
    newest_tokens,failed=fetch_tokens(rpc,new,sleep_s)
    older=[]
    if not history_done and not first:
        older,ended=backfill_page(rpc,back_before,size)
        old_tokens,failed_old=fetch_tokens(rpc,older,sleep_s)
        newest_tokens.update(old_tokens);failed+=failed_old
        history_done=ended
        back_before=older[-1]['signature'] if older and not ended else None
    nxt={'revision':'ORACLE_508_V2','head':next_head,'backfill_before':back_before,
         'history_complete':history_done,'last_success_unix':time.time()}
    result={'status':'PASS_BOOTSTRAP' if first else 'PASS_INCREMENTAL',
            'signatures_new':len(new),'signatures_backfilled':len(older),
            'tokens_observed':len(newest_tokens),'skipped_failed_signatures':failed,
            'history_complete':history_done,'head_updated':next_head!=head,
            'read_only':True,'signing':False,'broadcast':False,
            'transaction_version_max':TX_CONFIG['maxSupportedTransactionVersion']}
    return result,nxt,newest_tokens


def tests():
    class Fake:
        def __init__(self, fail=False):
            self.sigs=[{'signature':'s'+str(i),'err':None} for i in range(7,0,-1)]
            self.configs=[];self.fail=fail
        def __call__(self,method,params):
            if method=='getSignaturesForAddress':
                opts=params[1]; rows=self.sigs[:]
                if opts.get('before'): rows=rows[next(i for i,r in enumerate(rows) if r['signature']==opts['before'])+1:]
                if opts.get('until'): rows=rows[:next(i for i,r in enumerate(rows) if r['signature']==opts['until'])]
                return rows[:opts['limit']]
            self.configs.append(params[1])
            if self.fail: raise RuntimeError('RPC {"code":-32015}')
            return {'version':1,'meta':{'postTokenBalances':[{'mint':'A'*32}]}}
    f=Fake(); r,c,t=capture(f,{},size=3,pages=3,sleep_s=0)
    assert r['status']=='PASS_BOOTSTRAP' and not c['history_complete'] and c['head']=='s7'
    assert c['backfill_before']=='s5' and f.configs and all(x['maxSupportedTransactionVersion']==1 for x in f.configs)
    r,c,t=capture(f,c,size=3,pages=3,sleep_s=0)
    assert r['signatures_backfilled']==3 and not c['history_complete'] and c['backfill_before']=='s2'
    r,c,t=capture(f,c,size=3,pages=3,sleep_s=0)
    assert r['signatures_backfilled']==1 and c['history_complete']
    f.sigs.insert(0,{'signature':'s8','err':None})
    r,c,t=capture(f,c,size=3,pages=3,sleep_s=0)
    assert r['signatures_new']==1 and c['head']=='s8'
    try: capture(Fake(fail=True),{},size=2,sleep_s=0)
    except RuntimeError: pass
    else: raise AssertionError('EXPECTED_RPC_HOLD')
    try: capture(Fake(),{'head':'s1'},size=2,pages=1,sleep_s=0)
    except RuntimeError as e: assert str(e)=='INCREMENTAL_GAP_PAGE_LIMIT'
    else: raise AssertionError('EXPECTED_GAP_HOLD')
    print('[PASS] ORACLE508_V2 v1_read pagination backfill cursor gap_hold failed_transaction')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true')
    ap.add_argument('--audit',action='store_true');a=ap.parse_args()
    if a.test: tests();return
    if not a.audit: ap.error('specify --audit or --test')
    checkpoint=read_json(CHECKPOINT,{})
    try:
        result,nxt,new_tokens=capture(engine._rpc,checkpoint)
        old=read_json(TOKENS,{})
        old.update(new_tokens)
        atomic_json(TOKENS,old)
        atomic_json(CHECKPOINT,nxt)
        result.update({'known_mriya_tokens':len(old),
           'live_tape_candidates':len(engine.tape_candidates(Path.cwd()))})
    except Exception as exc:
        msg=str(exc); code=re.search(r'"code"\s*:\s*(-?\d+)',msg)
        result={'status':'RPC_HOLD','error_type':type(exc).__name__,
            'rpc_code':int(code.group(1)) if code else None,
            'reason':msg if msg in ('TRANSACTION_MISSING','TRANSACTION_VERSION_UNEXPECTED',
             'INCREMENTAL_GAP_PAGE_LIMIT','PAGINATION_STALLED','PAGINATION_DUPLICATE') else 'RPC_OR_STATE_FAILURE',
            'read_only':True,'signing':False,'broadcast':False}
    atomic_json(STATE,result)
    print('[ORACLE508]',json.dumps(result,sort_keys=True))
    print('[REPORT]',STATE)
    if not result['status'].startswith('PASS_'):raise SystemExit(2)

if __name__=='__main__':main()
'''

def main():
    engine=Path('qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/engine.py')
    if not TARGET.parent.is_dir() or not engine.is_file():raise SystemExit('HOLD_REPO_PATH_MISSING')
    content=engine.read_text(encoding='utf-8')
    for required in ('def raw_candidate_universe(', 'def _tx_mints(', 'MRIYA='):
        if required not in content:raise SystemExit('HOLD_ENGINE_CONTRACT_DRIFT')
    ast.parse(SOURCE)
    TARGET.write_text(SOURCE,encoding='utf-8')
    print('[PASS] ORACLE508_V2_FULL_INSTALL scanner_unchanged no_signing no_broadcast')
    print('[INSTALLED]',TARGET)

if __name__=='__main__':main()
