
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid

BASE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_015_rpc_efficient_bootstrap.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json')
VERSION='ORACLE_015_RPC_EFFICIENT_TWO_VENUE_BOOTSTRAP'
CANARY=10_000_000
MAX_RPC=80
MAX_SIM=1

SAFE={
    'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT',
    'TEMP','TMP','COMSPEC','QSB_SOLANA_WALLET',
    'SOLANA_RPC_URL','QSB_SOLANA_RPC_URL'
}


def scrub(env):
    return {
        key:value for key,value in env.items()
        if key.upper() in SAFE
    }


def prepare_pairs_only(root,pd=None):
    if pd is None:
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd

    pairs,landing=pd.prepare_pairs(root)
    pairs=list(pairs or [])

    if not pairs:
        raise RuntimeError(
            'NO_EXACT_PUMPSWAP_DLMM_PAIRS'
        )

    registry=pd.account_registry(pairs)
    expected=set()

    for i,pair in enumerate(pairs):
        if not all((
            pair.token,
            pair.pump_pool,
            pair.meteora_pool,
            pair.pump_base_vault,
            pair.pump_quote_vault
        )):
            raise RuntimeError('INCOMPLETE_PAIR')

        watched={
            pair.pump_base_vault,
            pair.pump_quote_vault,
            pair.meteora_pool
        }

        watched.update(
            str(a[1]) for a in pair.arrays
        )
        expected.update(watched)

        if not watched.issubset(set(registry)):
            raise RuntimeError(
                'PAIR_ACCOUNT_COVERAGE_MISSING'
            )

        if any(registry[a][0]!=i for a in watched):
            raise RuntimeError(
                'PAIR_REGISTRY_WRONG_INDEX'
            )

    if set(registry)!=expected:
        raise RuntimeError(
            'UNRELATED_OR_MISSING_ACCOUNT_IN_REGISTRY'
        )

    state={
        'pairs':pairs,
        'preg':registry,
        'addresses':list(registry),
        'landing':landing,
        'eps':{},
        'creg':{},
        'xreg':{},
        'observed':{}
    }

    return state,{
        'two_venue':True,
        'ready_pairs':len(pairs),
        'watched_accounts':len(registry)
    }


class Guard:
    def __init__(self,rpc,limit=MAX_RPC):
        self.rpc=rpc
        self.limit=limit
        self.methods={}
        self.total=0
        self.simulations=0

    def __call__(self,method,params):
        if (
            not isinstance(method,str)
            or not (
                method.startswith('get')
                or method=='simulateTransaction'
            )
        ):
            raise RuntimeError(
                'NON_READONLY_RPC_REFUSED'
            )

        if self.total>=self.limit:
            raise RuntimeError(
                'RPC_REQUEST_BUDGET_EXHAUSTED'
            )

        if (
            method=='simulateTransaction'
            and self.simulations>=MAX_SIM
        ):
            raise RuntimeError(
                'SIMULATION_LIMIT_EXHAUSTED'
            )

        self.total+=1
        self.methods[method]=(
            self.methods.get(method,0)+1
        )

        if method=='simulateTransaction':
            self.simulations+=1

        return self.rpc(method,params)


def child(root,seconds,run_id):
    if any(
        'PRIVATE_KEY' in k.upper()
        or 'SECRET_KEY' in k.upper()
        for k in os.environ
    ):
        raise RuntimeError(
            'SECRET_REACHED_ISOLATED_CHILD'
        )

    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as v14
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

    if (
        not hasattr(v14,'build_bound')
        or not hasattr(v14,'child')
    ):
        raise RuntimeError(
            'V14_NATIVE_REBIND_NOT_INSTALLED'
        )

    guard=Guard(core.rpc)
    core.rpc=guard
    q25.prepare_once=prepare_pairs_only

    try:
        code=v14.child(root,seconds,run_id)
    finally:
        core.rpc=guard.rpc

    path=root/REPORT
    result=json.loads(
        path.read_text(encoding='utf-8')
    )

    if result.get('run_id')!=run_id:
        raise RuntimeError(
            'STALE_CLOSEOUT_REPORT'
        )

    result['two_venue_bootstrap']=VERSION
    result['rpc_ceiling']=MAX_RPC
    result['rpc_budget_used']=guard.total
    result['rpc_counts_measured']=guard.methods
    result['rpc_simulations_measured']=guard.simulations

    tmp=path.with_suffix('.budget.tmp')
    tmp.write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True
        )+'\n',
        encoding='utf-8'
    )
    tmp.replace(path)

    return code


class Tests(unittest.TestCase):

    def test_no_secrets(self):
        self.assertEqual(
            scrub({
                'PATH':'ok',
                'QSB_SOLANA_PRIVATE_KEY':'secret'
            }),
            {'PATH':'ok'}
        )

    def test_exact_canary(self):
        self.assertEqual(CANARY,10_000_000)

    def test_readonly_guard(self):
        g=Guard(lambda m,p:{})

        with self.assertRaisesRegex(
            RuntimeError,'REFUSED'
        ):
            g('sendTransaction',[])

        self.assertEqual(g.total,0)

    def test_ceiling(self):
        g=Guard(lambda m,p:{},2)
        g('getAccountInfo',[])
        g('getAccountInfo',[])

        with self.assertRaisesRegex(
            RuntimeError,'BUDGET'
        ):
            g('getAccountInfo',[])

        self.assertEqual(g.total,2)

    def test_single_sim(self):
        g=Guard(lambda m,p:{})
        g('simulateTransaction',[])

        with self.assertRaisesRegex(
            RuntimeError,'SIMULATION_LIMIT'
        ):
            g('simulateTransaction',[])

        self.assertEqual(g.simulations,1)

    def test_venue_only_coverage(self):
        from types import SimpleNamespace as S

        p=S(
            token='t',
            pump_pool='p',
            meteora_pool='m',
            pump_base_vault='v1',
            pump_quote_vault='v2',
            arrays=[(-8,'a',b'')]
        )

        pd=S(
            prepare_pairs=lambda root:([p],5000),
            account_registry=lambda pairs:{
                'v1':(0,'PUMP_BASE'),
                'v2':(0,'PUMP_QUOTE'),
                'm':(0,'DLMM_POOL'),
                'a':(0,'DLMM_ARRAY_0')
            }
        )

        state,cap=prepare_pairs_only('.',pd)

        self.assertEqual(
            cap['watched_accounts'],4
        )
        self.assertEqual(
            set(state['addresses']),
            {'v1','v2','m','a'}
        )

    def test_extra_account_rejected(self):
        from types import SimpleNamespace as S

        p=S(
            token='t',
            pump_pool='p',
            meteora_pool='m',
            pump_base_vault='v1',
            pump_quote_vault='v2',
            arrays=[]
        )

        pd=S(
            prepare_pairs=lambda root:([p],0),
            account_registry=lambda pairs:{
                'v1':(0,'PUMP_BASE'),
                'v2':(0,'PUMP_QUOTE'),
                'm':(0,'DLMM_POOL'),
                'unrelated':(0,'ORCA')
            }
        )

        with self.assertRaisesRegex(
            RuntimeError,'UNRELATED'
        ):
            prepare_pairs_only('.',pd)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--probe',action='store_true')
    ap.add_argument('--child',action='store_true')
    ap.add_argument('--seconds',type=int,default=15)
    ap.add_argument('--run-id',default='')

    a=ap.parse_args()
    root=Path.cwd()

    if a.test:
        result=unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                Tests
            )
        )
        return 0 if result.wasSuccessful() else 1

    if a.child:
        sys.path.insert(0,str(root))
        return child(root,a.seconds,a.run_id)

    if a.probe:
        if not 10<=a.seconds<=20:
            print(
                '[HOLD] PROBE_WINDOW_MUST_BE_10_TO_20_SECONDS'
            )
            return 2

        run_id=str(uuid.uuid4())

        cmd=[
            sys.executable,
            '-I',
            str(Path(__file__).resolve()),
            '--child',
            '--seconds',
            str(a.seconds),
            '--run-id',
            run_id
        ]

        try:
            proc=subprocess.run(
                cmd,
                cwd=root,
                env=scrub(os.environ),
                capture_output=True,
                text=True,
                timeout=a.seconds+60
            )

            record=json.loads(
                (root/REPORT).read_text(
                    encoding='utf-8'
                )
            )

            if (
                record.get('run_id')!=run_id
                or record.get('two_venue_bootstrap')!=VERSION
            ):
                raise RuntimeError(
                    'WRONG_OR_STALE_REPORT'
                )

            for k in (
                'status',
                'ready',
                'priced_events',
                'evaluations',
                'best_quotes',
                'attempts',
                'holds',
                'rpc_budget_used',
                'rpc_counts_measured',
                'rpc_simulations_measured'
            ):
                print(
                    '['+k.upper()+']',
                    json.dumps(record.get(k))
                )

            print(
                '[RPC_CEILING]',MAX_RPC,
                '[MAX_SIM]',MAX_SIM,
                '[SIGNING] FALSE [BROADCAST] FALSE'
            )

            return proc.returncode

        except Exception as exc:
            print(
                '[HOLD] BOOTSTRAP_DIAGNOSTIC',
                type(exc).__name__
            )
            return 2

    dst=root/BASE/NAME

    if not dst.parent.is_dir():
        print(
            '[FAIL] CANONICAL_EXECUTOR_PACKAGE_MISSING'
        )
        return 1

    if dst.resolve()!=Path(__file__).resolve():
        shutil.copyfile(
            Path(__file__).resolve(),
            dst
        )

    print('[PASS]',VERSION,dst)
    print(
        '[MODE] TWO_VENUE_HYDRATION; '
        'SCANNER_UNCHANGED; RPC_CEILING',
        MAX_RPC
    )
    print(
        '[SIGNING] FALSE '
        '[BROADCAST] FALSE '
        '[ALT_MUTATION] FALSE'
    )
    return 0


if __name__=='__main__':
    raise SystemExit(main())
