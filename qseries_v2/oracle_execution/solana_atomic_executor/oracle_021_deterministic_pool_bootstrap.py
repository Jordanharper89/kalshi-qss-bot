
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid

PACKAGE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST='oracle_021_deterministic_pool_bootstrap.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_021_POOL_BOOTSTRAP.json')
V17_REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_017_SESSION.json')
ATOMIC_REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json')
VERSION='ORACLE_021_DETERMINISTIC_POOL_LIVE_VERIFICATION'
SAFE={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','COMSPEC',
      'QSB_SOLANA_WALLET','SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL'}


def clean_env(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}


def derived_pool(token,core):
    from solders.pubkey import Pubkey
    base=Pubkey.from_string(str(token))
    quote=Pubkey.from_string(core.WSOL)
    pfun=Pubkey.from_string(core.PUMP_FUN)
    amm=Pubkey.from_string(core.PUMP)
    authority,_=Pubkey.find_program_address([b'pool-authority',bytes(base)],pfun)
    pool,_=Pubkey.find_program_address([
        b'pool',(0).to_bytes(2,'little'),bytes(authority),bytes(base),bytes(quote)
    ],amm)
    return str(pool)


def attest(raw,owner,token,core):
    if owner!=core.PUMP:
        raise RuntimeError('PUMP_POOL_PROGRAM_OWNER_MISMATCH')
    dec=core.decode_pump_pool(raw)
    if dec['base_mint']!=token:
        raise RuntimeError('PUMP_POOL_BASE_MINT_MISMATCH')
    if dec['quote_mint']!=core.WSOL:
        raise RuntimeError('PUMP_POOL_QUOTE_MINT_MISMATCH')
    return True


def audit(root,core):
    rows=core.tape_candidates(root)
    seen=set(); matched=0; mismatched=0; invalid=0
    for token,pool in rows:
        if (token,pool) in seen:continue
        seen.add((token,pool))
        try:
            if derived_pool(token,core)==pool:matched+=1
            else:mismatched+=1
        except (ValueError,TypeError,KeyError):
            invalid+=1
    return {'tape_candidates':len(seen),'pda_matches':matched,
            'pda_mismatches':mismatched,'invalid_pubkeys':invalid,
            'rpc_requests':0,'onchain_activity_certified':False}


def persist(root,report):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    tmp.replace(path)


def child(root,seconds,run_id):
    report={'version':VERSION,'run_id':run_id,'status':'HOLD',
            'signing':False,'broadcast':False,'canary_sent':False,
            'scanner_source_unchanged':True,'rpc_budget':80,'sim_limit':1}
    if any('PRIVATE_KEY' in x.upper() or 'SECRET_KEY' in x.upper() for x in os.environ):
        report['hold']='SECRET_ENVIRONMENT_REFUSED'
        persist(root,report)
        return 2
    sys.path.insert(0,str(root))
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_017_persistent_guarded_session as v17
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_015_rpc_efficient_bootstrap as v15
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as atomic
    report['offline_identity_audit']=audit(root,core)
    if not report['offline_identity_audit']['pda_matches']:
        report['hold']='NO_DETERMINISTIC_MATCHED_TAPE_POOLS'
        persist(root,report)
        return 2
    if (v15.MAX_RPC,v15.MAX_SIM,v15.CANARY)!=(80,1,10_000_000):
        report['hold']='READONLY_GUARD_DRIFT'
        persist(root,report)
        return 2
    if not getattr(atomic,'VERSION','').startswith('ORACLE_ATOMIC_CLOSEOUT_V20_'):
        report['hold']='V20_NATIVE_GATE_NOT_INSTALLED'
        persist(root,report)
        return 2
    original_check=engine.exact_pool_ok
    original_account=core.account
    checked={}
    stats={'pda_admitted':0,'pda_rejected':0,'pump_onchain_validated':0,
           'pump_onchain_rejected':0,'pump_account_read_failed':0}

    def deterministic_check(token,pool):
        try:
            match=derived_pool(token,core)==pool
        except (TypeError,ValueError,KeyError):
            match=False
        if not match:
            stats['pda_rejected']+=1
            return False,'PUMP_PDA_MISMATCH'
        if pool in checked and checked[pool]!=token:
            stats['pda_rejected']+=1
            return False,'PUMP_POOL_TOKEN_CONFLICT'
        checked[pool]=token
        stats['pda_admitted']+=1
        return True,'PDA_MATCH_REQUIRES_ONCHAIN_VERIFICATION'

    def guarded_account(address):
        try:
            raw,owner=original_account(address)
        except Exception:
            if address in checked:stats['pump_account_read_failed']+=1
            raise
        if address in checked:
            try:
                attest(raw,owner,checked[address],core)
            except Exception:
                stats['pump_onchain_rejected']+=1
                raise
            stats['pump_onchain_validated']+=1
        return raw,owner

    engine.exact_pool_ok=deterministic_check
    core.account=guarded_account
    started=time.monotonic()
    try:
        v17.child(root,seconds,run_id)
        previous=json.loads((root/V17_REPORT).read_text(encoding='utf-8'))
        atomic_report=json.loads((root/ATOMIC_REPORT).read_text(encoding='utf-8'))
        if previous.get('run_id')!=run_id or atomic_report.get('run_id')!=run_id:
            raise RuntimeError('STALE_INTEGRATION_REPORT')
        report.update(
            scanner_status=previous.get('status'),
            ready=previous.get('ready',0),
            scanner=previous.get('scanner') or {},
            evaluations=previous.get('evaluations') or {},
            priced_events=previous.get('priced_events',0),
            rpc_requests=previous.get('rpc_requests',0),
            rpc_by_method=previous.get('rpc_by_method') or {},
            simulations=previous.get('simulations',0),
            atomic_status=atomic_report.get('status'),
            local_check_count=atomic_report.get('local_check_count',0),
            local_check_pass=atomic_report.get('local_check_pass',0),
            local_rejections=atomic_report.get('local_check_reject') or {},
            attempts=atomic_report.get('attempts') or [],
            holds=atomic_report.get('holds') or [],
            elapsed_seconds=round(time.monotonic()-started,2),
            identity_validation=stats.copy()
        )
        if report['rpc_requests']>80 or report['simulations']>1:
            report['hold']='BUDGET_EXCEEDED'
        elif report['ready']==0:
            report['hold']='ZERO_HYDRATED_PAIRS_AFTER_VERIFICATION'
        elif previous.get('status')!='SCANNER_ACTIVE_EXECUTION_UNCERTIFIED':
            report['hold']='SCANNER_PRICING_NOT_CERTIFIED'
        else:
            report['status']='SCANNER_ACTIVE_NATIVE_GATE_UNCERTIFIED'
        persist(root,report)
        return 0
    except Exception as ex:
        report['hold']='BOOTSTRAP_'+type(ex).__name__
        report['identity_validation']=stats.copy()
        persist(root,report)
        return 2
    finally:
        engine.exact_pool_ok=original_check
        core.account=original_account


def parent(root,seconds):
    run_id=str(uuid.uuid4())
    cmd=[sys.executable,'-I',str(Path(__file__).resolve()),
         '--child','--seconds',str(seconds),'--run-id',run_id]
    try:
        proc=subprocess.run(cmd,cwd=root,env=clean_env(os.environ),
                            capture_output=True,text=True,timeout=seconds+150)
        record=json.loads((root/REPORT).read_text(encoding='utf-8'))
        if record.get('run_id')!=run_id:raise RuntimeError('STALE_REPORT')
        for key in ('status','hold','offline_identity_audit','identity_validation',
                    'scanner_status','ready','scanner','priced_events',
                    'evaluations','rpc_requests','rpc_by_method','simulations',
                    'atomic_status','local_check_count','local_check_pass',
                    'local_rejections','attempts','holds'):
            if key in record:print('['+key.upper()+']',json.dumps(record[key]),flush=True)
        print('[SCANNER] ORIGINAL [RPC_MAX] 80 [SIM_MAX] 1 [SIGNING] FALSE [BROADCAST] FALSE',flush=True)
        print('[REPORT]',root/REPORT,flush=True)
        return proc.returncode
    except Exception as ex:
        print('[HOLD] PARENT_'+type(ex).__name__,flush=True)
        return 2


class Tests(unittest.TestCase):
    def test_env_private_key_never_passed(self):
        self.assertEqual(clean_env({'PATH':'x','QSB_SOLANA_PRIVATE_KEY':'secret'}),{'PATH':'x'})
    def test_rpc_passed_without_logging(self):
        self.assertEqual(clean_env({'SOLANA_RPC_URL':'hidden'}),{'SOLANA_RPC_URL':'hidden'})
    def test_current_pool_formula(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from solders.pubkey import Pubkey
        token=core.WSOL
        pool=derived_pool(token,core)
        self.assertEqual(len(bytes(Pubkey.from_string(pool))),32)
    def test_wrong_owner_refused(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        with self.assertRaisesRegex(RuntimeError,'OWNER'):
            attest(b'', 'incorrect','token',core)
    def test_base_mint_refused(self):
        class C:
            PUMP='p'; WSOL='w'
            @staticmethod
            def decode_pump_pool(raw):return {'base_mint':'bad','quote_mint':'w'}
        with self.assertRaisesRegex(RuntimeError,'BASE_MINT'):
            attest(b'', 'p','good',C())
    def test_quote_mint_refused(self):
        class C:
            PUMP='p'; WSOL='w'
            @staticmethod
            def decode_pump_pool(raw):return {'base_mint':'good','quote_mint':'bad'}
        with self.assertRaisesRegex(RuntimeError,'QUOTE_MINT'):
            attest(b'', 'p','good',C())
    def test_good_owner_and_mints(self):
        class C:
            PUMP='p'; WSOL='w'
            @staticmethod
            def decode_pump_pool(raw):return {'base_mint':'good','quote_mint':'w'}
        self.assertTrue(attest(b'', 'p','good',C()))
    def test_offline_audit_only(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        r=audit(Path.cwd(),core)
        self.assertEqual(r['rpc_requests'],0)
        self.assertEqual(r['tape_candidates'],r['pda_matches']+r['pda_mismatches']+r['invalid_pubkeys'])
    def test_no_trade_functions(self):
        import inspect
        source=inspect.getsource(child)
        self.assertNotIn('sendTransaction',source)
        self.assertNotIn('sign_transaction',source)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--audit',action='store_true')
    ap.add_argument('--child',action='store_true')
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--seconds',type=int,default=60)
    ap.add_argument('--run-id',default='')
    args=ap.parse_args();root=Path.cwd()
    if args.test:
        results=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if results.wasSuccessful() else 1
    if args.audit:
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        print('[OFFLINE_IDENTITY]',json.dumps(audit(root,core),sort_keys=True))
        return 0
    if args.child:return child(root,args.seconds,args.run_id)
    if args.run:
        if not 45<=args.seconds<=120:
            print('[HOLD] DURATION_45_TO_120_SECONDS');return 2
        return parent(root,args.seconds)
    dest=root/PACKAGE/DEST
    if not dest.parent.is_dir():
        print('[HOLD] CANONICAL_PACKAGE_MISSING');return 2
    if dest.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),dest)
    print('[PASS]',VERSION,dest)
    print('[MODE] DETERMINISTIC_PDA_DISCOVERY; ONCHAIN_PUMP_ATTESTATION; SCANNER_UNCHANGED')
    print('[SIGNING] FALSE [BROADCAST] FALSE [CANARY] UNSENT')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
