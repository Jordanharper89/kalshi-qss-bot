from __future__ import annotations
"""ORACLE-503 secure-wallet simulation launcher atop canonical ORACLE-502 engine.
No broadcast, no private keys in source, files, shell history, or reports.
"""
import argparse, getpass, importlib, json, math, os, time
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_503_sim_credential_store as vault

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
REPORT=BASE/'oracle_503_atomic_sim_machine.json'
PKG='qseries_v2.oracle_execution.solana_atomic_executor.'
class Hold(RuntimeError): pass

def _wallet_for_run(args):
    if args.signed_sim:
        pub,secret=vault.load_signer()
        if args.wallet and args.wallet!=pub:raise Hold('REQUESTED_PUBLIC_WALLET_DOES_NOT_MATCH_SAVED_SIGNER')
        del secret
        return pub,None
    if args.wallet:
        from solders.pubkey import Pubkey
        try:Pubkey.from_string(args.wallet)
        except Exception:raise Hold('INVALID_PUBLIC_WALLET') from None
        return args.wallet,None
    pub,secret=vault.load_signer()
    return pub,None

def _budget_gate(row,producer,epoch,*,prior,budget_lamports,reserve_lamports,now_ms=None):
    why=prior(row,producer,epoch,now_ms=now_ms)
    if why:return why
    size=row.get('size_lamports')
    if type(size) is not int or size not in range(10_000_000,100_000_001,5_000_000):return 'HOLD_NOT_IN_19_SIZE_GRID'
    if size>budget_lamports-reserve_lamports:return 'HOLD_SIZE_EXCEEDS_BUDGET_AFTER_FEE_RESERVE'
    return None

def run(args):
    if not 30<=args.seconds<=3600:raise Hold('SECONDS_OUT_OF_RANGE')
    if any(not math.isfinite(x) for x in (args.budget_sol,args.reserve_sol)):
        raise Hold('NONFINITE_BUDGET')
    budget=round(args.budget_sol*1e9); reserve=round(args.reserve_sol*1e9)
    if budget<=reserve+10_000_000 or budget>10_000_000_000 or reserve<0:
        raise Hold('INVALID_RESEARCH_BUDGET')
    wallet,_unused=_wallet_for_run(args)
    # The canonical V502 engine imports must happen after setting provider URLs.
    helius=getpass.getpass('Helius API key (hidden): ').strip()
    if not helius:raise Hold('HELIUS_KEY_REQUIRED')
    os.environ['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+helius
    os.environ['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+helius
    os.environ['QSB_LIVE_ARM']='NO'
    os.environ['QSB_SOLANA_WALLET']=wallet
    os.environ.pop('QSB_SOLANA_PRIVATE_KEY',None)
    del helius
    helper=importlib.import_module(PKG+'oracle_502_atomic_sim_machine')
    hb=helper.wait_for_scanner(args.wait_seconds)
    exe=importlib.import_module(PKG+'oracle_503_execution_engine')
    if not callable(getattr(exe,'precheck',None)) or not callable(getattr(exe,'work',None)):
        raise Hold('CANONICAL_EXECUTOR_MODULE_INCOMPLETE')
    prior=exe.precheck
    def checked(row,producer,epoch,now_ms=None):
        return _budget_gate(row,producer,epoch,prior=prior,budget_lamports=budget,
                            reserve_lamports=reserve,now_ms=now_ms)
    exe.precheck=checked
    try:
        # The ORACLE503 engine fetches the signer directly from Credential Manager.
        # NO_SHARED_ENV_SECRET: No secret is put into any process environment.
        print('[ORACLE503_EXECUTOR] '+json.dumps({'wallet_public':wallet,
            'wallet_source':'WINDOWS_CREDENTIAL_MANAGER' if args.signed_sim or not args.wallet else 'PUBLIC_CLI',
            'producer_prefix':str(hb.get('producer',''))[:12],'epoch':hb.get('epoch'),
            'budget_ceiling_sol':args.budget_sol,'reserve_sol':args.reserve_sol,
            'signed_sim_requested':bool(args.signed_sim),'broadcast':False,
            'risk_adjusted_optimal_size_certified':False},sort_keys=True),flush=True)
        rc=exe.work(args.seconds,wallet,signed_sim=args.signed_sim)
        p=BASE/'oracle_503_native_engine.json'
        try:res=json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
        except (OSError,ValueError):res={}
        out={'mode':'SIMULATION_ONLY','broadcast':False,'wallet_public':wallet,
            'source_epoch':hb.get('epoch'),'signed_sim_requested':bool(args.signed_sim),
            'native_engine':helper.safe_status(res),'funded_execution':False}
        BASE.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(out,sort_keys=True,indent=2),encoding='utf-8')
        print('[ORACLE503_FINAL] '+json.dumps(out,sort_keys=True),flush=True)
        return rc
    finally:
        exe.precheck=prior
        os.environ.pop('QSB_SOLANA_PRIVATE_KEY',None)

def main():
    p=argparse.ArgumentParser(description='ORACLE503 Windows secure saved simulation signer')
    group=p.add_mutually_exclusive_group(required=True)
    for mode in ('test','create-signer','save-signer','show-wallet','delete-signer','run'):
        group.add_argument('--'+mode,action='store_true')
    p.add_argument('--signed-sim',action='store_true')
    p.add_argument('--seconds',type=int,default=600)
    p.add_argument('--wait-seconds',type=int,default=90)
    p.add_argument('--wallet',default='')
    p.add_argument('--budget-sol',type=float,default=0.105)
    p.add_argument('--reserve-sol',type=float,default=0.005)
    a=p.parse_args()
    try:
        if a.test:
            vault.tests()
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_502_atomic_sim_machine as m
            m.tests()
            assert _budget_gate({'size_lamports':100_000_000},'p',1,prior=lambda *args,**k:None,
                    budget_lamports=105_000_000,reserve_lamports=5_000_000) is None
            assert _budget_gate({'size_lamports':100_000_000},'p',1,prior=lambda *args,**k:None,
                    budget_lamports=40_000_000,reserve_lamports=5_000_000)=='HOLD_SIZE_EXCEEDS_BUDGET_AFTER_FEE_RESERVE'
            print('[PASS] ORACLE503 complete launcher and credential boundary tests')
            return 0
        if a.create_signer:
            from solders.keypair import Keypair
            pair=Keypair()
            pub=vault.save_signer(str(pair))
            print('[VAULT_SAVED] PUBLIC_WALLET='+pub+'; TEST_ONLY; PRIVATE_KEY_NOT_PRINTED')
            print('[RECOVERY] Credential is tied to Windows profile; losing the profile can lose the signing key. Do not fund this disposable wallet.')
            return 0
        if a.save_signer:
            secret=getpass.getpass('PRIVATE signing key to save to Windows Credential Manager (hidden): ')
            public=vault.save_signer(secret)
            del secret
            print('[VAULT_SAVED] PUBLIC_WALLET='+public+'; PRIVATE_KEY_NOT_PRINTED')
            return 0
        if a.show_wallet:
            pub,_=vault.load_signer()
            print('[SAVED_PUBLIC_WALLET] '+pub)
            return 0
        if a.delete_signer:
            vault.delete_signer()
            print('[VAULT_DELETED] Simulation-only wallet credential erased')
            return 0
        if a.run:return run(a)
    except (Hold,vault.VaultHold) as exc:
        print('[ORACLE503_HOLD] '+str(exc),flush=True);return 2
    except KeyboardInterrupt:
        print('[ORACLE503_HOLD] INPUT_CANCELLED',flush=True);return 130
    except Exception as exc:
        # Never stringify arbitrary native/RPC errors, which may embed secret URLs.
        print('[ORACLE503_HOLD] '+type(exc).__name__,flush=True);return 2
    return 2
if __name__=='__main__':raise SystemExit(main())
