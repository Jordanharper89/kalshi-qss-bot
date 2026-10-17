from __future__ import annotations
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

def select_research_row(report, rows, token=None):
    # The scanner may rotate staged_discovery.json after a certified Mriya
    # candidate is hydrated. The durable V10 witness names the token; a fresh
    # on-chain-reverified crosslist reconstructs pool identity for research.
    tokens=report.get('staged_tokens',[]) if isinstance(report,dict) else []
    if not isinstance(tokens,list) or any(not isinstance(t,str) for t in tokens):
        raise RuntimeError('V10_STAGED_TOKENS_INVALID')
    if token is None:
        unique=set(tokens)
        if len(unique)!=1:raise RuntimeError('SPECIFY_TOKEN_OR_ONE_V10_STAGED_TOKEN_REQUIRED')
        token=next(iter(unique))
    if not isinstance(token,str) or not 32<=len(token)<=44:
        raise RuntimeError('INVALID_TARGET_TOKEN')
    hits=[]
    for r in rows:
        if not isinstance(r,dict) or r.get('token')!=token:continue
        if not all(isinstance(r.get(k),str) and 32<=len(r[k])<=44 for k in ('token','pump_pool','meteora_pool')):
            continue
        hits.append(r)
    triples={(r['token'],r['pump_pool'],r['meteora_pool']) for r in hits}
    if not triples:raise RuntimeError('TOKEN_NOT_IN_CURRENT_CROSSVENUE_UNIVERSE')
    if len(triples)!=1:raise RuntimeError('AMBIGUOUS_LIVE_CROSSVENUE_ROUTE')
    t,p,m=next(iter(triples))
    return {'token':t,'pump_pool':p,'meteora_pool':m,
            'source':'V10_STAGED_TOKEN_CURRENT_CROSSLIST_REVERIFIED',
            'risk_scope':'RESEARCH_ONLY_TOKEN_RISK_NOT_EXECUTION_CERTIFIED'}

def research_route(token=None):
    # Use the token explicitly staged by V10 as an identity hint; DO NOT use
    # the rotating stage file as live evidence. Rediscover now, then verify
    # the exact PumpSwap and Meteora programs and mint identities on-chain.
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine as e
    p=BASE/'final_boss_v10_admission_stage.json'
    if not p.is_file() or p.is_symlink() or p.stat().st_size>200000:
        raise RuntimeError('V10_ADMISSION_WITNESS_MISSING')
    report=json.loads(p.read_text(encoding='utf-8'))
    if report.get('stage_written') is not True or report.get('status')!='STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE':
        raise RuntimeError('V10_ADMISSION_WITNESS_NOT_STAGED')
    rows=e.candidate_universe(ROOT)
    row=select_research_row(report,rows,token)
    return row

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
    r=research_route(token)
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
        'source':'LIVE_REDISCOVERED_AND_ONCHAIN_REVERIFIED_ROUTE','market_cap_type':'ONCHAIN_TOTAL_SUPPLY_FDV_PROXY_NOT_CIRCULATING_CAP',
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
        def test_stage_rotation_keeps_route_researchable(self):
            t='T'*38;p='P'*38;m='M'*38
            x=select_research_row({'staged_tokens':[t]},[{'token':t,'pump_pool':p,'meteora_pool':m}],None)
            self.assertEqual((x['token'],x['pump_pool'],x['meteora_pool']),(t,p,m))
        def test_staged_token_must_exist_in_live_crosslist(self):
            try:select_research_row({'staged_tokens':['T'*38]},[{'token':'Z'*38,'pump_pool':'P'*38,'meteora_pool':'M'*38}],None)
            except RuntimeError as ex:self.assertEqual(str(ex),'TOKEN_NOT_IN_CURRENT_CROSSVENUE_UNIVERSE')
            else:self.fail('UNVERIFIED_ROUTE_ADMITTED')
        def test_ambiguous_exact_pools_hold(self):
            t='T'*38
            rr=[{'token':t,'pump_pool':'P'*38,'meteora_pool':z*38} for z in ('M','Z')]
            try:select_research_row({'staged_tokens':[t]},rr,None)
            except RuntimeError as ex:self.assertEqual(str(ex),'AMBIGUOUS_LIVE_CROSSVENUE_ROUTE')
            else:self.fail('AMBIGUOUS_ROUTE_ADMITTED')
        def test_multiple_tokens_require_explicit_selection(self):
            try:select_research_row({'staged_tokens':['T'*38,'Z'*38]},[],None)
            except RuntimeError as ex:self.assertEqual(str(ex),'SPECIFY_TOKEN_OR_ONE_V10_STAGED_TOKEN_REQUIRED')
            else:self.fail('UNKNOWN_TOKEN_ADMITTED')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise RuntimeError('V17_FIXTURE_TEST_FAILED')
    print('[PASS] V17B 14 fixtures including stage-rotation and exact live-route identity',flush=True)

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
