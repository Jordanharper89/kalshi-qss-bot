from __future__ import annotations
"""Full V17 read-only exact-pool size/depth/risk audit installer.
No scanner, event-bus, executor, or signing changes. Windows CMD, Python 3.14.
"""
import argparse, ast, hashlib, os, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v17_size_risk_audit.py'
SOURCE = r'''from __future__ import annotations
"""Standalone V17 source-isolated live sizing certificate; never authorizes execution."""
import argparse, json, math, os, struct, time
from pathlib import Path

ROOT=Path.cwd()
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
REPORT=BASE/'final_boss_v17_size_risk_audit.json'
SIZES=tuple(round(0.010+0.005*i,3) for i in range(19))
TOKEN22='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'

def qualify(op, *, pump_base, pump_quote, fdv_sol, budget_lamports,
            fee_ceiling_lamports, max_pool_bps, max_fdv_bps, max_bins):
    """Hard constraints, then maximize estimated *absolute* fee-adjusted SOL."""
    start=int(op.get('start',0)); gross=int(op.get('local_net',-10**18))
    d=op.get('direction'); mq=op.get('mq') or {}
    reasons=[]
    if d not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):reasons.append('UNKNOWN_DIRECTION')
    if start not in [round(x*1e9) for x in SIZES]:reasons.append('NOT_ON_CERTIFIED_GRID')
    if start>budget_lamports:reasons.append('WALLET_BUDGET')
    if not isinstance(fdv_sol,(float,int)) or not math.isfinite(fdv_sol) or fdv_sol<=0:
        reasons.append('FDV_PROXY_UNAVAILABLE')
    elif (start/1e9)*10000>float(fdv_sol)*max_fdv_bps:
        reasons.append('FDV_EXPOSURE')
    bins=mq.get('bins_crossed')
    if type(bins) is not int or bins<1 or bins>max_bins:reasons.append('DLMM_DEPTH_BINS')
    if not pump_base or not pump_quote:reasons.append('PUMP_RESERVES_INVALID')
    elif d=='PUMP_TO_METEORA':
        if start*10000>pump_quote*max_pool_bps:reasons.append('PUMP_QUOTE_RESERVE_IMPACT')
    else:
        token_in=int(op.get('net_token') or 0)
        if token_in<=0 or token_in*10000>pump_base*max_pool_bps:
            reasons.append('PUMP_BASE_RESERVE_IMPACT')
    minend=op.get('local_min_end')
    if d=='METEORA_TO_PUMP' and isinstance(minend,int) and minend<=start+fee_ceiling_lamports:
        reasons.append('PUMP_MIN_OUT_INSUFFICIENT')
    if gross-fee_ceiling_lamports<=0:reasons.append('NONPOSITIVE_FEE_ADJUSTED')
    return {'direction':d,'size_sol':start/1e9,'start_lamports':start,
            'gross_lamports':gross,'fee_ceiling_lamports':fee_ceiling_lamports,
            'estimated_fee_adjusted_lamports':gross-fee_ceiling_lamports,
            'bins_crossed':bins,'holds':reasons,'screen_pass':not reasons,
            'execution_authority':False}

def rank(rows):
    eligible=[x for x in rows if x['screen_pass']]
    return max(eligible,key=lambda x:(x['estimated_fee_adjusted_lamports'],-x['start_lamports'])) if eligible else None

def staged_route(token=None):
    p=BASE/'staged_discovery.json'
    if not p.is_file() or p.is_symlink() or p.stat().st_size>1_000_000:
        raise RuntimeError('STAGED_DISCOVERY_MISSING_OR_UNTRUSTED')
    doc=json.loads(p.read_text(encoding='utf-8'))
    rows=doc.get('rows',[]) if isinstance(doc,dict) else []
    if not isinstance(rows,list):raise RuntimeError('STAGED_ROWS_INVALID')
    stage=[r for r in rows if isinstance(r,dict) and r.get('source')=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'
           and all(isinstance(r.get(k),str) for k in ('token','pump_pool','meteora_pool'))]
    if token:
        stage=[r for r in stage if r['token']==token]
    if not stage:raise RuntimeError('NO_VERIFIED_STAGED_ROUTE_FOR_AUDIT')
    if not token and len({r['token'] for r in stage})!=1:
        raise RuntimeError('MULTIPLE_STAGED_TOKENS_SPECIFY_TOKEN')
    return stage[0]

def verified_meteora_meta(c,r):
    tok,pump,pool=[r[k] for k in ('token','pump_pool','meteora_pool')]
    for k in (tok,pump,pool):c.b58d(k)
    raw,owner=c.account(pump)
    if owner!=c.PUMP:raise RuntimeError('PUMP_OWNER_HOLD')
    decoded=c.decode_pump_pool(raw)
    if decoded['base_mint']!=tok or decoded['quote_mint']!=c.WSOL:
        raise RuntimeError('PUMP_PAIR_MINT_HOLD')
    _,owner=c.account(pool)
    if owner!=c.DLMM:raise RuntimeError('DLMM_OWNER_HOLD')
    j=c.http('https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query='+tok)
    rows=j.get('data',[]) if isinstance(j,dict) else j
    matches=[]
    for x in rows if isinstance(rows,list) else []:
        if not isinstance(x,dict) or (x.get('address') or x.get('pool_address') or x.get('pubkey'))!=pool:
            continue
        a=x.get('token_x') or x.get('tokenX') or {}
        b=x.get('token_y') or x.get('tokenY') or {}
        def mint(v):return v if isinstance(v,str) else (v.get('address') or v.get('mint') or v.get('token_address')) if isinstance(v,dict) else None
        mx,my=mint(a),mint(b)
        if {mx,my}!={tok,c.WSOL}:raise RuntimeError('DLMM_MINT_MISMATCH')
        xx,ox=c.account(mx);yy,oy=c.account(my)
        if ox not in (c.TOKEN,c.TOKEN22) or oy not in (c.TOKEN,c.TOKEN22) or len(xx)<82 or len(yy)<82:
            raise RuntimeError('TOKEN_MINT_OWNER_HOLD')
        matches.append({'address':pool,'token_x':mx,'token_y':my,
                        'decimals_x':xx[44],'decimals_y':yy[44]})
    if len(matches)!=1:raise RuntimeError('DLMM_ROUTE_NOT_UNIQUE')
    return matches[0]

def live_audit(budget_sol,fee_ceiling_lamports,max_pool_bps,max_fdv_bps,max_bins,token=None):
    if not isinstance(budget_sol,float) or not 0.010<=budget_sol<=10:
        raise RuntimeError('EXPLICIT_BUDGET_REQUIRED')
    if not 5000<=fee_ceiling_lamports<=2_000_000:
        raise RuntimeError('EXPLICIT_FEE_CEILING_REQUIRED')
    if not (1<=max_pool_bps<=1000 and 1<=max_fdv_bps<=100 and 1<=max_bins<=32):
        raise RuntimeError('INVALID_RISK_LIMITS')
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine as e
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    if not os.environ.get('SOLANA_RPC_URL','').startswith('https://mainnet.helius-rpc.com/'):
        raise RuntimeError('HELIUS_RPC_REQUIRED')
    if SIZES!=tuple(round(0.010+i*0.005,3) for i in range(19)) or not callable(q18.exact_snapshot_opportunities):
        raise RuntimeError('EXACT_PRICE_GRID_GUARD')
    r=staged_route(token)
    meta=verified_meteora_meta(c,r)
    original=e.candidate_universe
    e.candidate_universe=lambda root:[dict(r,meteora_meta=meta)]
    try: pairs,_=pd.prepare_pairs(ROOT)
    finally:e.candidate_universe=original
    exact=[p for p in pairs if (p.token,p.pump_pool,p.meteora_pool)==(r['token'],r['pump_pool'],r['meteora_pool'])]
    if len(exact)!=1:raise RuntimeError('LIVE_SINGLE_PAIR_HYDRATION_HOLD')
    p=exact[0]
    mint,owner=c.account(p.token)
    if owner not in (c.TOKEN,c.TOKEN22) or len(mint)<82:raise RuntimeError('TOKEN_MINT_INVALID')
    supply=struct.unpack_from('<Q',mint,36)[0];decimals=int(mint[44])
    if not supply or decimals>18 or not p.pump_base_reserve or not p.pump_quote_reserve:
        raise RuntimeError('MARKET_SIZE_INPUT_INVALID')
    fdv_sol=(supply/pow(10,decimals))*(p.pump_quote_reserve/1e9)/(p.pump_base_reserve/pow(10,decimals))
    snap=q20._pair_snapshot(p)
    warm=q18.worker()
    try:
        warm.warm(p.pump_pool)
        rows=[];exceptions={}
        for size in SIZES:
            try:
                for op in q18.exact_snapshot_opportunities(snap,size):
                    rows.append(qualify(op,pump_base=p.pump_base_reserve,pump_quote=p.pump_quote_reserve,
                        fdv_sol=fdv_sol,budget_lamports=round(budget_sol*1e9),
                        fee_ceiling_lamports=fee_ceiling_lamports,max_pool_bps=max_pool_bps,
                        max_fdv_bps=max_fdv_bps,max_bins=max_bins))
            except Exception as exc:
                key=type(exc).__name__
                exceptions[key]=exceptions.get(key,0)+1
    finally:
        try:warm.close()
        except Exception:pass
    best=rank(rows)
    # Token2022 status is a hard execution hold until extension semantics and an atomic signed sim are certified.
    token_risk='TOKEN2022_REQUIRES_EXTENSION_CERTIFICATION' if owner==c.TOKEN22 else 'SPL_MINT_NO_FULL_TOKEN_AUDIT'
    status=('HOLD_TOKEN2022_EXECUTION_CERTIFICATION' if owner==c.TOKEN22 else 'RESEARCH_BEST_ONLY_NOT_EXECUTABLE') if best else 'HOLD_NO_RISK_ADMISSIBLE_SIZE'
    report={'status':status,'token':p.token,'pump_pool':p.pump_pool,'meteora_pool':p.meteora_pool,
        'source':'LIVE_REHYDRATED_STAGED_EXACT_ROUTE','market_cap_type':'ONCHAIN_TOTAL_SUPPLY_FDV_PROXY_NOT_CIRCULATING_CAP',
        'fdv_proxy_sol':round(fdv_sol,6),'mint_program':owner,'mint_decimals':decimals,
        'risk_scope':r.get('risk_scope'),'token_risk':token_risk,
        'pump_base_reserve_raw':p.pump_base_reserve,'pump_quote_reserve_sol':p.pump_quote_reserve/1e9,
        'dlmm_bin_arrays':len(p.arrays),'size_grid_sol':list(SIZES),'quotes_complete':len(rows),
        'quote_failures':exceptions,'budget_sol':budget_sol,'max_pool_participation_bps':max_pool_bps,
        'max_fdv_exposure_bps':max_fdv_bps,'max_bin_crossings':max_bins,
        'fee_ceiling_lamports':fee_ceiling_lamports,'best_research_size':best,
        'all_sizes':rows,'min_out_full_two_leg_certified':False,
        'priority_fee_estimate_from_signed_transaction':False,'atomic_simulation_pass':False,
        'wallet_funding_verified':False,'broadcast':False,'execution_authority':False,
        'observed_at':time.time()}
    BASE.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    shown=dict(report);shown.pop('all_sizes')
    print('[V17_LIVE_SIZE_RISK_AUDIT] '+json.dumps(shown,sort_keys=True),flush=True)
    print('[REPORT]',REPORT,flush=True)
    return report

def tests():
    import unittest
    class T(unittest.TestCase):
        def fixture(self,**overrides):
            op=dict(direction='PUMP_TO_METEORA',start=10_000_000,local_net=100_000,mq={'bins_crossed':2})
            op.update(overrides)
            return qualify(op,pump_base=10**12,pump_quote=2*10**9,fdv_sol=1000,
                           budget_lamports=40_000_000,fee_ceiling_lamports=50_000,
                           max_pool_bps=100,max_fdv_bps=10,max_bins=8)
        def test_good(self):self.assertTrue(self.fixture()['screen_pass'])
        def test_fee(self):self.assertFalse(self.fixture(local_net=49_999)['screen_pass'])
        def test_pool(self):self.assertIn('PUMP_QUOTE_RESERVE_IMPACT',self.fixture(start=100_000_000)['holds'])
        def test_fdv(self):
            x=self.fixture();self.assertEqual(x['estimated_fee_adjusted_lamports'],50_000)
        def test_budget(self):self.assertIn('WALLET_BUDGET',self.fixture(start=100_000_000)['holds'])
        def test_bin(self):self.assertIn('DLMM_DEPTH_BINS',self.fixture(mq={'bins_crossed':9})['holds'])
        def test_minout(self):
            x=self.fixture(direction='METEORA_TO_PUMP',net_token=1000,local_min_end=10_000_000)
            self.assertIn('PUMP_MIN_OUT_INSUFFICIENT',x['holds'])
        def test_absolute_net_not_bps(self):
            a=dict(self.fixture(),screen_pass=True,estimated_fee_adjusted_lamports=100,start_lamports=10_000_000)
            b=dict(self.fixture(),screen_pass=True,estimated_fee_adjusted_lamports=200,start_lamports=20_000_000)
            self.assertIs(rank([a,b]),b)
        def test_no_candidate(self):self.assertIsNone(rank([self.fixture(local_net=-1)]))
        def test_grid(self):self.assertEqual((len(SIZES),SIZES[0],SIZES[-1]),(19,.010,.100))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise RuntimeError('V17_FIXTURE_TEST_FAILED')
    print('[PASS] V17 exact SDK sizing audit fixtures; output is research only',flush=True)

def main():
    a=argparse.ArgumentParser()
    group=a.add_mutually_exclusive_group(required=True)
    group.add_argument('--test',action='store_true')
    group.add_argument('--audit',action='store_true')
    a.add_argument('--budget-sol',type=float)
    a.add_argument('--fee-ceiling-lamports',type=int)
    a.add_argument('--max-pool-bps',type=int,default=100)
    a.add_argument('--max-fdv-bps',type=int,default=10)
    a.add_argument('--max-bin-crossings',type=int,default=8)
    a.add_argument('--token')
    x=a.parse_args()
    try:
        if x.test:tests()
        else:
            if x.budget_sol is None or x.fee_ceiling_lamports is None:
                raise RuntimeError('EXPLICIT_BUDGET_AND_FEE_CEILING_REQUIRED')
            live_audit(x.budget_sol,x.fee_ceiling_lamports,x.max_pool_bps,x.max_fdv_bps,x.max_bin_crossings,x.token)
        return 0
    except Exception as exc:
        print('[V17_HOLD]',type(exc).__name__+':'+str(exc)[:180],flush=True)
        return 2
if __name__=='__main__':raise SystemExit(main())
'''

def install():
    ast.parse(SOURCE)
    if TARGET.exists():
        if TARGET.read_text(encoding='utf-8')!=SOURCE:
            raise RuntimeError('V17_OUTPUT_ALREADY_EXISTS_WITH_DIFFERENT_SOURCE')
        print('[V17_VERIFIED_EXISTING]',TARGET)
        return
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='\n',dir=TARGET.parent,suffix='.tmp',delete=False) as f:
        f.write(SOURCE);tmp=Path(f.name)
    try: os.replace(tmp,TARGET)
    finally:tmp.unlink(missing_ok=True)
    print('[PASS] V17_FULL_READ_ONLY_SIZE_AUDITOR_INSTALLED')
    print('[MODULE]',TARGET)
    print('[SHA256]',hashlib.sha256(SOURCE.encode('utf-8')).hexdigest())
    print('[PRESERVED] V16/ORACLE322/Q18/Q20/Q25/ORACLE402; no signing; no broadcast')

def main():
    a=argparse.ArgumentParser()
    mode=a.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test',action='store_true')
    mode.add_argument('--install',action='store_true')
    z=a.parse_args()
    try:
        ast.parse(SOURCE)
        if z.test:
            import subprocess,sys
            with tempfile.TemporaryDirectory() as h:
                p=Path(h)/'audit.py';p.write_text(SOURCE,encoding='utf-8')
                r=subprocess.run([sys.executable,str(p),'--test'])
                if r.returncode:raise RuntimeError('V17_TEST_FAILED')
            print('[PASS] V17 source and deterministic 10-test audit',flush=True)
        else:install()
        return 0
    except Exception as exc:
        print('[V17_INSTALL_HOLD]',type(exc).__name__+':'+str(exc)[:160],flush=True)
        return 2
if __name__=='__main__':raise SystemExit(main())
