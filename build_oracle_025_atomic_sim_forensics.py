
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, threading, unittest, uuid

PACKAGE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_025_atomic_sim_forensics.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_025_SIM_FORENSICS.json')
PREVIOUS=Path('runtime_state/oracle/oracle_live_execution/ORACLE_024_FRESH_CANDIDATES.json')
VERSION='ORACLE_025_SINGLE_SIM_INNER_TRANSFER_FORENSICS'
SAFE={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','COMSPEC',
      'SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL','QSB_SOLANA_WALLET'}

def safe_environment(src):
    return {k:v for k,v in src.items() if k.upper() in SAFE}

def write(root,data):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    tmp.replace(path)

def parse_amount(info):
    value=info.get('amount')
    if value is None:
        value=(info.get('tokenAmount') or {}).get('amount')
    try:return int(value)
    except (TypeError,ValueError):return None

def extract_transfers(inner,source,destination):
    summary=[]
    for group in inner or []:
        if not isinstance(group,dict):continue
        for ix in group.get('instructions') or []:
            if not isinstance(ix,dict):continue
            parsed=ix.get('parsed') or {}
            if not isinstance(parsed,dict):continue
            if not str(parsed.get('type','')).lower().startswith('transfer'):continue
            info=parsed.get('info') or {}
            if not isinstance(info,dict):continue
            amount=parse_amount(info)
            if amount is None:continue
            src=info.get('source');dst=info.get('destination')
            role=('PUMP_TO_WALLET_TOKEN' if dst==source else
                  'WALLET_TOKEN_TO_METEORA' if src==source else
                  'METEORA_TO_WALLET_WSOL' if dst==destination else 'OTHER')
            if role=='OTHER':continue
            summary.append({'outer_instruction':group.get('index'),
                            'role':role,'raw_transfer_amount':amount,
                            'token_2022':ix.get('programId')=='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
                            'transfer_type':str(parsed.get('type'))})
    return summary

def error_code(value):
    if not isinstance(value,dict):return 'NONE' if value is None else 'OTHER'
    row=value.get('InstructionError')
    if isinstance(row,list) and len(row)==2 and isinstance(row[1],dict):
        code=row[1].get('Custom')
        if isinstance(code,int):return 'IX_%s_CUSTOM_%s'%(row[0],code)
    return 'OTHER'

def analyze(evidence,bounds):
    rows=evidence.get('transfers') or []
    totals={name:sum(x['raw_transfer_amount'] for x in rows if x['role']==name)
            for name in ('PUMP_TO_WALLET_TOKEN','WALLET_TOKEN_TO_METEORA','METEORA_TO_WALLET_WSOL')}
    out={'error_code':evidence.get('error_code'),'transfers':rows,
         'raw_transfer_totals':totals,'cpi_available':bool(evidence.get('cpi_available')),
         'protected_minimum_lamports':bounds.get('native_minimum_output'),
         'locally_replayed_output_lamports':bounds.get('native_quoted_output'),
         'native_input_token_units':bounds.get('native_token_input'),
         'quoted_input_token_units':bounds.get('quoted_token_input'),
         'fee_reserve_lamports':bounds.get('fee_reserve'),
         'no_swap_success_or_profit_claim':True}
    if evidence.get('error_code','').endswith('_CUSTOM_6003'):
        out['classification']='SWAP2_MIN_OUT_REJECTED'
        attempted=totals['METEORA_TO_WALLET_WSOL']
        if attempted:
            out['attempted_wsol_transfer_lamports']=attempted
            out['attempted_output_minus_minimum']=attempted-int(bounds.get('native_minimum_output') or 0)
        else:
            out['classification']='SWAP2_6003_NO_OUTPUT_TRANSFER_IN_CPI'
    elif evidence.get('error_code')=='NONE':
        out['classification']='SIM_SUCCESS_FEES_AND_RESIDUE_UNCERTIFIED'
    else:
        out['classification']='OTHER_SIMULATION_RESULT'
    if any(x['token_2022'] for x in rows):
        out['token_2022_transfer_fees_not_deducible_from_raw_amounts']=True
    return out

def child(root,seconds,run_id):
    rep={'version':VERSION,'run_id':run_id,'status':'HOLD',
         'signing':False,'broadcast':False,'canary_sent':False,'profit_certified':False,
         'simulation_cap':1,'fee_and_residue_certified':False}
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        rep['hold']='SECRET_ENV_REFUSED';write(root,rep);return 2

    sys.path.insert(0,str(root))
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_024_fresh_candidate_revalidation as v24
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as v20

    if not v20.VERSION.startswith('ORACLE_ATOMIC_CLOSEOUT_V20_'):
        rep['hold']='V20_NOT_INSTALLED';write(root,rep);return 2

    old_rpc=core.rpc
    old_build=v20.build_bound
    scope={'simulation_calls':0,'bound':{},'evidence':{},'addresses':{}}
    lock=threading.Lock()

    def captured_build(*args,**kwargs):
        ix,bounds=old_build(*args,**kwargs)
        matches=[x for x in ix if x.get('programId')==core.DLMM]
        if len(matches)!=1 or len(matches[0].get('accounts') or [])<16:
            raise RuntimeError('FORENSIC_METEORA_ACCOUNTS_UNAVAILABLE')
        m=matches[0];a=m['accounts']
        with lock:
            scope['bound']=dict(bounds)
            scope['addresses']={'token_in':a[4]['pubkey'],'wsol_out':a[5]['pubkey']}
        return ix,bounds

    def instrumented_rpc(method,params):
        if method!='simulateTransaction':return old_rpc(method,params)
        with lock:
            scope['simulation_calls']+=1
            if scope['simulation_calls']>1:
                raise RuntimeError('FORENSICS_SIM_CAP_EXCEEDED')
        if len(params)<2 or not isinstance(params[1],dict):
            raise RuntimeError('SIMULATION_OPTIONS_MISSING')

        options=dict(params[1])
        options['innerInstructions']=True
        patched=[params[0],options]
        result=old_rpc(method,patched)
        v=(result or {}).get('value') or {}

        with lock:
            addresses=dict(scope['addresses'])
            scope['evidence']={
                'error_code':error_code(v.get('err')),
                'cpi_available':isinstance(v.get('innerInstructions'),list),
                'compute_units':v.get('unitsConsumed'),
                'transfers':extract_transfers(
                    v.get('innerInstructions'),
                    addresses.get('token_in'),
                    addresses.get('wsol_out')
                )
            }
        return result

    core.rpc=instrumented_rpc
    v20.build_bound=captured_build
    try:
        ret=v24.child(root,seconds,run_id)
        previous=json.loads((root/PREVIOUS).read_text(encoding='utf-8'))
        if previous.get('run_id')!=run_id:
            raise RuntimeError('STALE_V24_REPORT')

        rep.update(
            ready=previous.get('ready'),
            priced_events=previous.get('priced_events'),
            rpc_requests=previous.get('rpc_requests'),
            simulations=previous.get('simulations'),
            positive_candidates=previous.get('positive_candidates'),
            native_passes=previous.get('native_passes'),
            previous_status=previous.get('status'),
            attempts=previous.get('attempts'),
            holds=previous.get('holds'),
            observed_simulation_calls=scope['simulation_calls']
        )

        if scope['evidence']:
            rep['forensics']=analyze(scope['evidence'],scope['bound'])
            rep['status']='FORENSICS_CAPTURED_NO_EXECUTION_AUTHORITY'
        elif previous.get('simulations'):
            rep['hold']='SIMULATION_RESPONSE_NOT_CAPTURED'
        else:
            rep['hold']='NO_PROFITABLE_CANDIDATE_REACHED_SIMULATION'

        if (rep.get('rpc_requests') or 0)>80 or (rep.get('simulations') or 0)>1:
            rep['status']='HOLD_INSTRUMENTED_BUDGET_EXCEEDED'
        write(root,rep)
        return ret

    except Exception as exc:
        rep['hold']='FORENSICS_'+type(exc).__name__
        write(root,rep)
        return 2

    finally:
        core.rpc=old_rpc
        v20.build_bound=old_build

def parent(root,seconds):
    run_id=str(uuid.uuid4())
    cmd=[sys.executable,'-I',str(Path(__file__).resolve()),'--child',
         '--seconds',str(seconds),'--run-id',run_id]
    proc=subprocess.run(
        cmd,cwd=root,env=safe_environment(os.environ),
        capture_output=True,text=True,timeout=seconds+180
    )
    p=root/REPORT
    if not p.is_file():raise RuntimeError('REPORT_MISSING')
    data=json.loads(p.read_text(encoding='utf-8'))
    if data.get('run_id')!=run_id:
        raise RuntimeError('STALE_FORENSICS_REPORT')
    for k in ('status','hold','ready','priced_events','rpc_requests','simulations',
              'positive_candidates','native_passes','forensics','attempts','holds'):
        if k in data:
            print('['+k.upper()+']',json.dumps(data[k],sort_keys=True),flush=True)
    print('[SCANNER] FROZEN [PROTECTED_MINIMUM] UNCHANGED [SIM_LIMIT] 1 [SIGNING] FALSE [BROADCAST] FALSE')
    print('[REPORT]',p)
    return proc.returncode

class Tests(unittest.TestCase):
    def test_env(self):
        self.assertEqual(
            safe_environment({'PATH':'good','QSB_SOLANA_PRIVATE_KEY':'secret'}),
            {'PATH':'good'}
        )

    def test_parse_checked_amount(self):
        self.assertEqual(parse_amount({'tokenAmount':{'amount':'300'}}),300)

    def test_parse_transfer_amount(self):
        self.assertEqual(parse_amount({'amount':'123'}),123)

    def test_error(self):
        self.assertEqual(
            error_code({'InstructionError':[5,{'Custom':6003}]}),
            'IX_5_CUSTOM_6003'
        )

    def test_inner_transfers(self):
        inner=[
            {'index':4,'instructions':[{
                'programId':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623V5DA',
                'parsed':{'type':'transferChecked','info':{
                    'source':'vault','destination':'userin',
                    'tokenAmount':{'amount':'17'}
                }}
            }]},
            {'index':5,'instructions':[
                {'programId':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623V5DA',
                 'parsed':{'type':'transferChecked','info':{
                     'source':'userin','destination':'reserve',
                     'tokenAmount':{'amount':'15'}
                 }}},
                {'programId':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623V5DA',
                 'parsed':{'type':'transferChecked','info':{
                     'source':'reserve2','destination':'userout',
                     'tokenAmount':{'amount':'100'}
                 }}}
            ]}
        ]
        rows=extract_transfers(inner,'userin','userout')
        self.assertEqual(
            [x['role'] for x in rows],
            ['PUMP_TO_WALLET_TOKEN',
             'WALLET_TOKEN_TO_METEORA',
             'METEORA_TO_WALLET_WSOL']
        )
        self.assertEqual(
            analyze(
                {'error_code':'IX_5_CUSTOM_6003','transfers':rows,'cpi_available':True},
                {'native_minimum_output':110}
            )['attempted_output_minus_minimum'],
            -10
        )

    def test_no_sim_result(self):
        self.assertEqual(
            analyze(
                {'error_code':'IX_5_CUSTOM_6003','transfers':[],'cpi_available':False},
                {}
            )['classification'],
            'SWAP2_6003_NO_OUTPUT_TRANSFER_IN_CPI'
        )

    def test_no_success_claim(self):
        self.assertTrue(
            analyze({'error_code':'NONE','transfers':[]},{})[
                'no_swap_success_or_profit_claim'
            ]
        )

    def test_bound_semantics(self):
        self.assertEqual(
            VERSION,
            'ORACLE_025_SINGLE_SIM_INNER_TRANSFER_FORENSICS'
        )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--child',action='store_true')
    ap.add_argument('--seconds',type=int,default=60)
    ap.add_argument('--run-id',default='')
    args=ap.parse_args()
    root=Path.cwd()

    if args.test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    if args.child:
        return child(root,args.seconds,args.run_id)

    if args.run:
        if not 45<=args.seconds<=90:
            print('[HOLD] DURATION_45_TO_90_SECONDS')
            return 2
        return parent(root,args.seconds)

    dst=root/PACKAGE/NAME
    if not dst.parent.is_dir():
        print('[HOLD] EXECUTOR_PACKAGE_MISSING')
        return 2
    if dst.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),dst)

    print('[PASS]',VERSION,dst)
    print('[MODE] FROZEN_SCANNER; SINGLE_SIM_CAPTURE; NATIVE_MIN_UNCHANGED')
    print('[SIGNING] FALSE [BROADCAST] FALSE [CANARY] UNSENT')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
