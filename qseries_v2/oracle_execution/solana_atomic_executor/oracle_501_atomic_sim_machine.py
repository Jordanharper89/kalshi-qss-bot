from __future__ import annotations
"""ORACLE-501: canonical event reader -> native 2-leg v0 -> signed SIM only.
No independent crosslist discovery, no funded broadcast, no custody actions.
"""
import argparse, getpass, importlib, json, os, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
REPORT=BASE/'oracle_501_atomic_sim_machine.json'
PKG='qseries_v2.oracle_execution.solana_atomic_executor.'
GRID=frozenset(range(10_000_000,100_000_001,5_000_000))
ADDR=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
WALLET_DEFAULT='7t4krNuD6e6srbZZh2pkMELy1mJSHFTM7HitbBm7vaBE'
class Hold(RuntimeError):pass

def budget_gate(row,producer,epoch,*,prior,budget_lamports,reserve_lamports,now_ms=None):
    reason=prior(row,producer,epoch,now_ms=now_ms)
    if reason:return reason
    size=row.get('size_lamports')
    if type(size) is not int or size not in GRID:return 'HOLD_NOT_IN_EXACT_SIZE_GRID'
    if type(budget_lamports) is not int or type(reserve_lamports) is not int:return 'HOLD_BUDGET_TYPE'
    if budget_lamports<=reserve_lamports+10_000_000:return 'HOLD_INSUFFICIENT_RESEARCH_BUDGET'
    if size>budget_lamports-reserve_lamports:return 'HOLD_SIZE_EXCEEDS_BUDGET_AFTER_FEE_RESERVE'
    if row.get('direction') not in ('METEORA_TO_PUMP','PUMP_TO_METEORA'):
        return 'HOLD_UNSUPPORTED_DIRECTION'
    return None

def source_health():
    sc=importlib.import_module(PKG+'oracle_344_scanner_align')
    conn=sc.bus()
    try:hb=sc.validate_scanner(conn)
    finally:conn.close()
    if not isinstance(hb,dict) or hb.get('ok') is not True:raise Hold('CANONICAL_SCANNER_NOT_HEALTHY')
    return hb

def wait_for_scanner(seconds=90):
    start=time.monotonic();last='CANONICAL_SCANNER_NOT_HEALTHY'
    while time.monotonic()-start<seconds:
        try:
            h=source_health();return h
        except (Hold,ImportError,RuntimeError,OSError) as e:
            last=type(e).__name__ if not isinstance(e,Hold) else str(e)
            time.sleep(1)
    raise Hold('SCANNER_NOT_READY_'+last[:40])

def safe_status(out):
    return {k:out.get(k) for k in ('status','phase','events_received','real_nominees',
        'native_attempts','native_unsigned','signed_sim_successes','native_holds',
        'source_holds','scanner_admitted_current','rebinds','signed_sim_protected_min_out')}

def run(args):
    if not ADDR.fullmatch(args.wallet):raise Hold('PUBLIC_WALLET_REQUIRED')
    if not 30<=args.seconds<=3600:raise Hold('SECONDS_OUT_OF_RANGE')
    budget=round(args.budget_sol*1_000_000_000)
    reserve=round(args.reserve_sol*1_000_000_000)
    if budget<=reserve+10_000_000 or budget>10_000_000_000 or reserve<0:
        raise Hold('RESEARCH_BUDGET_INVALID')
    hb=wait_for_scanner(args.wait_seconds)
    executor=importlib.import_module(PKG+'oracle_501_execution_engine')
    if not callable(getattr(executor,'work',None)) or not callable(getattr(executor,'precheck',None)):
        raise Hold('ORACLE402_CANONICAL_CONTRACT_MISSING')
    # Patch only THIS process's ingress selection. ORACLE402 still validates exact
    # producer, epoch, token, PumpSwap pool, DLMM pool, size and expiry at every gate.
    original=executor.precheck
    def guarded(row,producer,epoch,now_ms=None):
        return budget_gate(row,producer,epoch,prior=original,
            budget_lamports=budget,reserve_lamports=reserve,now_ms=now_ms)
    executor.precheck=guarded
    result=None
    try:
        k=getpass.getpass('Helius API key (hidden): ').strip()
        if not k:raise Hold('HELIUS_KEY_REQUIRED')
        os.environ['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+k
        os.environ['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+k
        k=None
        os.environ['QSB_LIVE_ARM']='NO'
        if args.signed_sim and not os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
            key=getpass.getpass('Solana signing key for SIMULATION ONLY (hidden): ').strip()
            if not key:raise Hold('SIM_SIGNER_REQUIRED')
            os.environ['QSB_SOLANA_PRIVATE_KEY']=key
            key=None
        print('[ORACLE501_EXECUTOR] '+json.dumps({'source':'ORACLE344_CANONICAL_SQLITE_EVENTS',
            'producer':str(hb.get('producer',''))[:12],'epoch':hb.get('epoch'),
            'budget_sol':args.budget_sol,'fee_reserve_sol':args.reserve_sol,
            'signed_sim_requested':args.signed_sim,'send_transaction':False,
            'scanner_discovery_called_by_ingress':False,'risk_adjusted_optimal_size_certified':False,
            'funded_execution':False},sort_keys=True),flush=True)
        # Original ORACLE402 builds an exact two-leg unsigned v0 ALT packet, uses
        # native proof_contract, and on explicit --signed-sim calls ORACLE401's
        # simulateTransaction only. Fee-adjusted P/L + residue checked there.
        rc=executor.work(args.seconds,args.wallet,signed_sim=args.signed_sim)
        p=BASE/'oracle_501_native_engine.json'
        try:result=json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None
        except (OSError,ValueError):pass
        out={'mode':'SIMULATION_ONLY','funded_execution':False,'broadcast':False,
            'source_epoch':hb.get('epoch'),'native_engine':safe_status(result or {}),
            'signed_sim_requested':args.signed_sim,
            'liquidity_and_market_cap_policy_certified':False,
            'first_funded_canary_authorized':False}
        BASE.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(out,sort_keys=True,indent=2),encoding='utf-8')
        print('[ORACLE501_FINAL] '+json.dumps(out,sort_keys=True),flush=True)
        return rc
    finally:executor.precheck=original

def tests():
    assert len(GRID)==19 and min(GRID)==10_000_000 and max(GRID)==100_000_000
    row={'size_lamports':10_000_000,'direction':'METEORA_TO_PUMP'}
    good=lambda row,producer,epoch,now_ms=None:None
    bad=lambda row,producer,epoch,now_ms=None:'HOLD_OLD_PRODUCER'
    assert budget_gate(row,'p',1,prior=good,budget_lamports=40_000_000,reserve_lamports=5_000_000) is None
    assert budget_gate(row,'p',1,prior=bad,budget_lamports=40_000_000,reserve_lamports=5_000_000)=='HOLD_OLD_PRODUCER'
    assert budget_gate(dict(row,size_lamports=40_000_000),'p',1,prior=good,budget_lamports=40_000_000,reserve_lamports=5_000_000)=='HOLD_SIZE_EXCEEDS_BUDGET_AFTER_FEE_RESERVE'
    assert budget_gate(dict(row,size_lamports=9_000_000),'p',1,prior=good,budget_lamports=40_000_000,reserve_lamports=5_000_000)=='HOLD_NOT_IN_EXACT_SIZE_GRID'
    assert budget_gate(dict(row,direction='BAD'),'p',1,prior=good,budget_lamports=40_000_000,reserve_lamports=5_000_000)=='HOLD_UNSUPPORTED_DIRECTION'
    assert budget_gate(row,'p',1,prior=good,budget_lamports=10_000_000,reserve_lamports=5_000_000)=='HOLD_INSUFFICIENT_RESEARCH_BUDGET'
    print('[PASS] ORACLE501 canonical source preserved, 19 sizes, budget and identity precedence, no broadcast')

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--test',action='store_true');m.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=600);p.add_argument('--wait-seconds',type=int,default=90)
    p.add_argument('--wallet',default=os.environ.get('QSB_SOLANA_WALLET',WALLET_DEFAULT))
    p.add_argument('--budget-sol',type=float,default=0.040);p.add_argument('--reserve-sol',type=float,default=0.005)
    p.add_argument('--signed-sim',action='store_true')
    args=p.parse_args()
    try:
        if args.test:tests();return 0
        return run(args)
    except Exception as exc:
        m=str(exc) if isinstance(exc,Hold) else type(exc).__name__
        print('[ORACLE501_HOLD] '+m[:110],flush=True);return 2
if __name__=='__main__':raise SystemExit(main())
