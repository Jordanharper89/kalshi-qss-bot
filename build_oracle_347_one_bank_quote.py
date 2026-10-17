"""ORACLE-347 full replacement installer; shadow-only."""
import argparse,hashlib,pathlib,py_compile,tempfile

TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_347_one_bank_quote.py')
SOURCE='"""ORACLE347 strict context-slot bank quote for nominated original direction/size."""\nimport time,collections\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old\nfrom qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge\nfrom qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder\nfrom qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18\n\ndef reprice(nom,cat,roles,rpc_url,decimals=None):\n    if not cat.get(\'discovery_complete\') or cat[\'bin_selected\']!=cat[\'bin_total\']:raise ValueError(\'ARRAY_CATALOG_INCOMPLETE\')\n    # A candidate\'s source slot acts as lower bound, NOT a same-slot assertion.\n    keys=sorted(k for k,rr in roles.items() if any(t==nom[\'token\'] for t,_ in rr))\n    if not 6<=len(keys)<=100:raise ValueError(\'BANK_ACCOUNT_COUNT_OUT_OF_BOUNDS\')\n    if not {\'PUMP_POOL\',\'DLMM_POOL\',\'PUMP_BASE_VAULT\',\'PUMP_QUOTE_VAULT\',\'DLMM_SOL_RESERVE\',\'DLMM_TOKEN_RESERVE\'}.issubset({role for k in keys for t,role in roles[k] if t==nom[\'token\']}):raise ValueError(\'BANK_REQUIRED_ROLES_MISSING\')\n    start=time.time_ns()\n    response=witness.rpc(rpc_url,\'getMultipleAccounts\',[keys,{\'encoding\':\'base64\',\'commitment\':\'processed\',\'minContextSlot\':int(nom[\'slot\'])}],collections.Counter(),retries=1)\n    rows,slot=bridge.bank_rows(response,keys,int(nom[\'slot\']),start)\n    if slot<int(nom[\'slot\']):raise ValueError(\'BANK_CONTEXT_BEHIND_SCANNER\')\n    if decimals is None:decimals=bridge.mint_metadata(rpc_url,[nom[\'token\']])\n    snap,lin=bridge.prepare_snapshot(cat,rows,roles,decimals,start-1,core,decoder)\n    if lin[\'slot_min\']!=slot or lin[\'slot_max\']!=slot:raise ValueError(\'BANK_MIXED_CONTEXT\')\n    quote=bridge.directional_ladder(snap,q18,core,requested=(nom[\'direction\'],nom[\'size_lamports\']/1e9))\n    exact=quote.get(\'requested_exact\')\n    if exact is None:raise ValueError(\'BANK_ORIGINAL_DIRECTION_UNPRICED\')\n    end=time.time_ns();elapsed=(end-start)/1e6\n    return dict(token=nom[\'token\'],direction=nom[\'direction\'],size_lamports=nom[\'size_lamports\'],scanner_slot=nom[\'slot\'],bank_slot=slot,scanner_gross=nom[\'gross_lamports\'],bank_gross=int(exact[\'gross_lamports\']),account_count=len(keys),single_context_verified=True,bank_elapsed_ms=round(elapsed,2),quote_ms=quote[\'quote_ms\'],gate=\'BANK_GROSS_POSITIVE\' if int(exact[\'gross_lamports\'])>0 and elapsed<=2000 else \'HOLD_NONPOSITIVE_OR_EXPIRED\',signing=False,broadcast=False)\n'
EXPECTED='edf9ebfb5d88f0986e4ba777f3291f2849d215bc83e79556ed5cdbe1b5263360'

def install():
    assert hashlib.sha256(SOURCE.encode()).hexdigest()==EXPECTED
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(SOURCE.encode())
    py_compile.compile(str(TARGET),doraise=True)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    print('[ORACLE347_INSTALL_PASS] '+str(TARGET));return 0

def test():
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)/TARGET.name
        p.write_bytes(SOURCE.encode())
        py_compile.compile(str(p),doraise=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
    assert 'sendTransaction' not in SOURCE and 'sign_transaction' not in SOURCE
    print('[ORACLE347_TEST_PASS] source,hash,syntax,no_send');return 0

def audit():
    assert EXPECTED==hashlib.sha256(SOURCE.encode()).hexdigest()
    print('[ORACLE347_AUDIT] FROZEN_SCANNER_UNTOUCHED SIGNING_FALSE BROADCAST_FALSE')
    return 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--install',action='store_true')
    p.add_argument('--test',action='store_true')
    p.add_argument('--audit',action='store_true')
    a=p.parse_args()
    if a.install:return install()
    if a.test:return test()
    if a.audit:return audit()
    p.error('SELECT_A_MODE')

if __name__=='__main__':raise SystemExit(main())