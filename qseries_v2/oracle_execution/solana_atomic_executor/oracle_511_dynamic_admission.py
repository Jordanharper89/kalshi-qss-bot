from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_509_exact_pair_qualification as q509
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_510_warm_pair_preflight as q510
from qseries_v2.oracle_execution.solana_atomic_executor import boss_scanner_live as scanner
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23

ROOT=Path('runtime_state/oracle/oracle_live_execution')
REPORT=ROOT/'oracle_511_dynamic_admission.json'
CAP=28

def assert_contract():
    if not callable(getattr(scanner,'select_rows',None)) or not hasattr(scanner,'STAGED'):
        raise RuntimeError('HOLD_SCANNER_STAGING_CONTRACT')
    if not callable(getattr(scanner,'audit',None)) or not hasattr(scanner,'BASELINE'):
        raise RuntimeError('HOLD_SCANNER_FREEZE_CONTRACT')
    frozen=scanner.audit()
    base=Path(scanner.BASELINE)
    if not base.is_file() or json.loads(base.read_text(encoding='utf-8'))!=frozen:
        raise RuntimeError('HOLD_SCANNER_FROZEN_HASH_MISMATCH')
    stage=Path(scanner.STAGED)
    if not str(stage).endswith('.json'):
        raise RuntimeError('HOLD_SCANNER_STAGE_PATH')
    return stage

def merger(existing,newcomers,cap=112):
    bykey={}
    for row in list(existing)+list(newcomers):
        if not isinstance(row,dict):continue
        t,p=row.get('token'),row.get('pump_pool')
        if not isinstance(t,str) or not isinstance(p,str) or len(t)<32 or len(p)<32:
            continue
        key=(t,p)
        if key not in bykey or row in newcomers:
            bykey[key]=dict(row)
    fresh=[bykey[(x['token'],x['pump_pool'])] for x in newcomers
           if (x['token'],x['pump_pool']) in bykey]
    keys={(x['token'],x['pump_pool']) for x in fresh}
    tail=[v for k,v in bykey.items() if k not in keys]
    return (fresh+tail)[:cap]

def watchable(ready,selected):
    seen={(x.get('token'),x.get('pump_pool')) for x in selected[:CAP]}
    return [x for x in ready if (x['token'],x['pump_pool']) in seen]

def prepare(limit):
    stage=assert_contract()
    lock=Path('runtime_state/oracle/final_boss_dual/scanner.lock')
    if lock.exists():
        raise RuntimeError('HOLD_SCANNER_LOCK_PRESENT_VERIFY_SCANNER_STOPPED')

    checks=q509.load(q510.CHECKS)
    candidates,total=q510.selected(checks,limit)
    if not candidates:
        raise RuntimeError('HOLD_NO_509_CANDIDATES')

    passed=[];failed=[]
    try:
        for row in candidates:
            try:
                warm=q510.warm_one(row)
                if {x['direction'] for x in warm['directions']}!=set(q510.DIRECTIONS):
                    raise RuntimeError('HOLD_INCOMPLETE_DIRECTIONS')
                passed.append((row,warm))
                print('[ORACLE511_PREWARM]',json.dumps({
                    'token':row['token'][:12],
                    'slot':warm['slot'],
                    'quotes':2
                }),flush=True)
            except Exception as exc:
                failed.append({
                    'token':row['token'][:12],
                    'error_type':type(exc).__name__,
                    'reason':str(exc) if isinstance(exc,q510.Hold)
                             else 'PREWARM_FAILED'
                })
                print('[ORACLE511_WARM_HOLD]',json.dumps(failed[-1]),flush=True)
    finally:
        for module in (q18,q23):
            worker=getattr(module,'_worker',None)
            if worker is not None:
                worker.close()
                module._worker=None

    if not passed:
        raise RuntimeError('HOLD_NO_LIVE_REWARMED_PAIR')

    existing=[]
    if stage.is_file():
        try:
            old=json.loads(stage.read_text(encoding='utf-8'))
            if (isinstance(old,dict) and
                isinstance(old.get('rows'),list) and
                0<=time.time()-float(old.get('generated_at',0))<=600):
                existing=old['rows'][:112]
        except (ValueError,OSError,TypeError):
            pass

    new=[]
    for row,warm in passed:
        source=('MRIYA_511_WARM'
                if 'MRIYA_COVERAGE' in row.get('sources',[])
                else 'LIVE_TAPE')
        new.append({
            'token':row['token'],
            'pump_pool':row['pump_pool'],
            'source':source,
            'age':0.0
        })

    staged=merger(existing,new)
    payload={
        'generated_at':time.time(),
        'rows':staged,
        'candidates':len(staged)
    }
    scanner.save(stage,payload)

    selected=scanner.select_rows([])
    visible=watchable(new,selected)
    if not visible:
        raise RuntimeError('HOLD_NOT_VISIBLE_IN_SCANNER_SELECTION')

    return {
        'staged_path':str(stage),
        'warm_pass':len(passed),
        'warm_holds':failed,
        'staged_rows':len(staged),
        'visible_in_first_28':len(visible),
        'visible_tokens':[r['token'] for r in visible],
        'stage_hash':hashlib.sha256(stage.read_bytes()).hexdigest(),
        'source_verified':total
    }

def trial(evidence,seconds):
    stage=Path(evidence['staged_path'])
    digest=hashlib.sha256(stage.read_bytes()).hexdigest()
    if digest!=evidence['stage_hash']:
        return {'status':'HOLD_STAGED_FILE_OVERRIDDEN'}

    if (not os.getenv('SOLANA_RPC_URL','').startswith('https://') or
        not os.getenv('SOLANA_WS_URL','').startswith('wss://')):
        return {'status':'HOLD_RPC_WS_REQUIRED'}

    cmd=[
        sys.executable,'-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.boss_scanner_live',
        '--run','--seconds',str(seconds),
        '--epochs','1','--pairs','28','--accounts','1280'
    ]

    print('[ORACLE511_TRIAL] bounded_single_epoch scanner_frozen '
          'no_signing no_broadcast',flush=True)

    env=os.environ.copy()
    env.pop('QSB_SOLANA_PRIVATE_KEY',None)
    env['QSB_LIVE_ARM']='NO'

    try:
        proc=subprocess.run(
            cmd,env=env,capture_output=True,text=True,
            timeout=seconds+110,errors='replace'
        )
    except subprocess.TimeoutExpired:
        return {'status':'HOLD_TRIAL_TIMEOUT'}

    warmed=set()
    quoted=set()
    heartbeats=0
    quote_count=0
    completed=False

    for line in (proc.stdout or '').splitlines():
        if '[BOSS322_EPOCH_END]' in line:
            try:
                end=json.loads(line.split('[BOSS322_EPOCH_END]',1)[1].strip())
                completed=completed or end.get('status')=='COMPLETED'
            except ValueError:
                pass

        if '[BOSS322_LIVE_MARKET]' in line:
            heartbeats+=1
            try:
                data=json.loads(line.split('[BOSS322_LIVE_MARKET]',1)[1].strip())
                quote_count=max(quote_count,int(data.get('quotes_010',0)))
                for quote in data.get('recent_quotes',[]) or []:
                    prefix=(str(quote.get('token',''))
                            if isinstance(quote,dict) else '')
                    if len(prefix)>=8:
                        quoted.update(
                            t for t in evidence['visible_tokens']
                            if t.startswith(prefix)
                        )
            except (ValueError,TypeError):
                pass

        if '[ORACLE025_TOKEN_WARM]' in line:
            warmed.update(
                t for t in evidence['visible_tokens']
                if t[:10] in line
            )

        if '[ORACLE020_EXACT_LATEST]' in line:
            quoted.update(
                t for t in evidence['visible_tokens']
                if t[:10] in line
            )

    passed=bool(
        proc.returncode==0 and
        completed and heartbeats and
        quote_count>0 and quoted
    )

    return {
        'status':('PASS_LIVE_EPOCH_OBSERVED'
                  if passed else 'HOLD_LIVE_ADMISSION_NOT_PROVEN'),
        'returncode':proc.returncode,
        'epoch_completed':completed,
        'market_heartbeats':heartbeats,
        'quotes_010_max':quote_count,
        'matched_warmed_tokens':sorted(warmed),
        'matched_quoted_tokens':sorted(quoted),
        'live_subscriptions_changed':bool(quoted)
    }

def tests():
    a={'token':'A'*32,'pump_pool':'P'*32,'source':'LIVE_TAPE'}
    b={'token':'B'*32,'pump_pool':'Q'*32,'source':'MRIYA_511_WARM'}
    staged=merger([a,a],[b],2)

    assert len(staged)==2
    assert staged[0]['token']==b['token']
    assert len(watchable([b],[a,b]))==1
    assert not watchable([b],[a])
    assert len(merger([a],[a],112))==1
    assert len(merger([a]*500,[b],112))<=112

    print('[PASS] ORACLE511 offline stage_dedupe '
          'cap28 visibility failclosed',flush=True)

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test',action='store_true')
    mode.add_argument('--audit',action='store_true')
    mode.add_argument('--trial',action='store_true')
    p.add_argument('--limit',type=int,default=3)
    p.add_argument('--seconds',type=int,default=90)
    args=p.parse_args()

    if args.test:
        tests()
        return

    if not 1<=args.limit<=7 or not 60<=args.seconds<=110:
        raise RuntimeError('HOLD_BOUNDS')
    if (os.getenv('QSB_SOLANA_PRIVATE_KEY') or
        os.getenv('QSB_LIVE_ARM','NO').upper()!='NO'):
        raise RuntimeError('HOLD_SECRET_ISOLATION')

    result={
        'status':'HOLD_PREPARE',
        'signing':False,
        'broadcast':False,
        'scanner_changed':False,
        'execution_authority':False
    }

    try:
        evidence=prepare(args.limit)
        result.update(evidence)
        result['status']='PASS_STAGE_SELECTOR_VISIBLE'
        result['live_subscriptions_changed']=False
        if args.trial:
            result.update(trial(evidence,args.seconds))
    except Exception as exc:
        reason=str(exc)
        result.update({
            'status':'HOLD_PREPARE',
            'reason':reason if reason.startswith('HOLD_')
                     else type(exc).__name__
        })

    q509.save(REPORT,result)
    print('[ORACLE511]',json.dumps({
        k:v for k,v in result.items()
        if k not in ('visible_tokens','stage_hash','warm_holds')
    },sort_keys=True),flush=True)
    print('[REPORT]',REPORT,flush=True)

    if not result['status'].startswith('PASS_'):
        raise SystemExit(2)

if __name__=='__main__':
    main()
