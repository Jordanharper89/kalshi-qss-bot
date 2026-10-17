"""ORACLE-302: inspect native Pump official quote bindings + sample canonical Meteora evidence.
Read-only, one batch, no substitutions for official PumpSwap economics.
"""
import argparse,ast,inspect,json,os,socket,sqlite3,time
from pathlib import Path
from collections import Counter
ROOT=Path('runtime_state/oracle/oracle_live_execution')
OUT=ROOT/'ORACLE302_CROSS_VENUE_CONTRACT.json'
CORE=Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
GRID=[round(.010+.005*i,3) for i in range(19)]

def check_disarmed():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')

def native_inventory(core=CORE):
    tree=ast.parse(core.read_text(encoding='utf-8'))
    names=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            if 'pump' in n.name.lower() or 'quote' in n.name.lower() or 'snapshot' in n.name.lower():
                names.append({'function':n.name,'line':n.lineno,'args':[a.arg for a in n.args.args],
                  'called':[ast.unparse(c.func) for c in ast.walk(n) if isinstance(c,ast.Call)][:16]})
    return sorted(names,key=lambda x:x['line'])

def pump_boundary(tree):
    good=[]
    for row in tree:
        n=row['function'].lower();args=set(row['args'])
        if 'pump' not in n or not ('quote' in n or 'price' in n):continue
        if {'amount_in','swap_for_y'}.issubset(args) or {'amount_in','direction'}.issubset(args):
            good.append(row)
    return good

def quote_guards(q,inp):
    if not isinstance(inp,int) or inp<=0:return 'INVALID_INPUT'
    rem=getattr(q,'remaining_in',None);out=getattr(q,'amount_out',None)
    if type(rem) is not int or type(out) is not int or rem<0 or rem>inp or out<=0:return 'UNVERIFIED_QUOTE_FIELDS'
    if rem:return 'PARTIAL_FILL'
    if getattr(q,'complete',None) is not True:return 'INCOMPLETE'
    return 'FULL_FILL'

def fail_closed_report(contract,selected):
    candidates=pump_boundary(contract)
    return {'build':'ORACLE302','status':'HOLD_OFFICIAL_PUMP_QUOTE_ENTRYPOINT_BINDING',
        'selected_accounts':selected,'native_pump_candidate_functions':candidates,
        'native_quoted_functions':[x for x in contract if 'quote' in x['function'].lower()],
        'required_bridge':['VERIFIED_NATIVE_PUMP_ACCOUNT_LAYOUT','OFFICIAL_PUMP_SWAP_QUOTE_ENTRYPOINT',
          'EXACT_TOKEN_INPUT_RAW','TWO_VENUE_FULL_FILL','FEE_ADJUSTED_NET'],
        'size_grid':GRID,'estimated_net_profit':None,'confirmed_arbitrage':0,
        'execution_admission':False,'signing':False,'broadcast':False}

def run():
    check_disarmed()
    import oracle_283_287_milestone_a_runtime as market
    import oracle_301_bidirectional_sdk_probe as meteora
    selected=market.targets()
    contract=native_inventory()
    report=fail_closed_report(contract,len(selected))
    # Reuse the physically demonstrated Meteora quote subsystem and its exact grid.
    if tuple(meteora.GRID)!=tuple(GRID):raise RuntimeError('PRICING_SIZE_GRID_CHANGED')
    report['meteora_two_leg_function']=meteora.two_quotes.__name__
    report['snapshot_dependency']='ORACLE299_BOUNDED_GETMULTIPLEACCOUNTS'
    report['verified_native_pump_quote_binding']=False
    # No dynamic guess-call into an unknown quote function. Executable cross-venue numbers must
    # come from an explicitly verified official SDK binding and account-layout contract.
    ROOT.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    summary={k:v for k,v in report.items() if k not in ('native_quoted_functions','native_pump_candidate_functions','size_grid')}
    summary['pump_candidate_functions']=len(report['native_pump_candidate_functions'])
    print('[ORACLE302_RESULT]',json.dumps(summary,sort_keys=True),flush=True)
    for row in report['native_pump_candidate_functions']:
        print('[ORACLE302_PUMP_BINDING]',json.dumps(row,sort_keys=True),flush=True)
    for row in report['native_quoted_functions'][:15]:
        print('[ORACLE302_QUOTE_ENTRYPOINT]',json.dumps({k:v for k,v in row.items() if k!='called'},sort_keys=True),flush=True)
    print('[REPORT]',OUT,flush=True)

def test():
    import tempfile
    class Q:remaining_in=0;amount_out=12;complete=True
    assert quote_guards(Q(),100)=='FULL_FILL'
    Q.remaining_in=1
    assert quote_guards(Q(),100)=='PARTIAL_FILL'
    Q.remaining_in=0;Q.complete=False
    assert quote_guards(Q(),100)=='INCOMPLETE'
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/'c.py'
        f.write_text('def pump_quote_snapshot(pool,amount_in,direction):\n return 1\n'
                     'def quote_meteora(state,amount_in):\n return 0\n',encoding='utf-8')
        inventory=native_inventory(f)
        assert len(pump_boundary(inventory))==1
        r=fail_closed_report(inventory,66)
        assert not r['execution_admission'] and r['estimated_net_profit'] is None
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
    print('[ORACLE302_TEST_PASS] local_source_contract=TRUE exact_grid=TRUE full_fill=TRUE partial_hold=TRUE no_orders=TRUE')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true');parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if args.test:test()
    elif args.run:run()
    else:parser.error('Specify --test or --run')
