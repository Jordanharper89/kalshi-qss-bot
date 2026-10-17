
"""ORACLE-505: full executor-only installer from verified local ORACLE-504 sources."""
from pathlib import Path
import ast
import os
import tempfile

P = Path('qseries_v2/oracle_execution/solana_atomic_executor')
FILES = ('oracle_504_targeted_native_hydration.py',
         'oracle_504_execution_engine.py', 'oracle_504_atomic_sim_machine.py')


def replace_one(src, old, new, label):
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f'HOLD_SOURCE_DRIFT_{label}: expected 1 anchor, saw {count}')
    return src.replace(old, new, 1)


def make():
    original = {}
    for f in FILES:
        path = P / f
        if not path.is_file():
            raise RuntimeError('HOLD_MISSING_504_SOURCE_' + f)
        original[f] = path.read_text(encoding='utf-8')
    hydration = original[FILES[0]]
    start = "    old=getattr(provider,'old',None)\n"
    end = "    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core\n"
    a = hydration.index(start, hydration.index('def exact_native_refresh('))
    b = hydration.index(end, a)
    original_block = hydration[a:b]
    if not all(x in original_block for x in ('TARGET_PROVIDER_BUILDER_NOT_INITIALIZED',
          'TARGET_NATIVE_BUILDER_CONTRACT_MISSING', 'TARGET_SINGLE_HYDRATION_CONTRACT_MISSING',
          'base_prepare=')):
        raise RuntimeError('HOLD_504_BUILDER_CONTRACT_CHANGED')
    bootstrap = '''def ensure_exact_builder(provider, candidate, expected_wallet):
    """Initialize lazy provider under a one-scanner-triple discovery scope.

    Only a fresh, exact canonical nomination may call this. Does not send a trade.
    """
    old=getattr(provider,'old',None)
    forward=getattr(provider,'forward',None)
    bootstrapped=old is None or forward is None
    if bootstrapped:
        warm=getattr(provider,'prewarm',None)
        if not callable(warm):
            raise TargetHold('TARGET_PROVIDER_PREWARM_METHOD_MISSING')
        try:
            with isolated_target_state(candidate):
                warm()
        except Exception as exc:
            raise classified('BUILDER_INIT',exc) from None
        old=getattr(provider,'old',None)
        forward=getattr(provider,'forward',None)
    if old is None or forward is None:
        raise TargetHold('TARGET_PROVIDER_BUILDER_NOT_INITIALIZED')
    if bootstrapped:
        pairs=getattr(forward,'pairs',None)
        if isinstance(pairs,dict) and any(t!=candidate['token'] for t in pairs):
            raise TargetHold('TARGET_BOOTSTRAP_UNRELATED_POOL_ADMITTED')
    needed=('install_proven_hot_math','prebuild_templates','prebuild_meteora_templates')
    if any(not callable(getattr(old,n,None)) for n in needed):
        raise TargetHold('TARGET_NATIVE_BUILDER_CONTRACT_MISSING')
    q25=getattr(old,'q25',None)
    q60b2=getattr(q25,'q60b2',None)
    q60b=getattr(q60b2,'q60b',None)
    base_prepare=getattr(q60b,'_ORIG_PREPARE',None)
    if not callable(base_prepare) or not callable(getattr(q25,'bind_cached_state',None)):
        raise TargetHold('TARGET_SINGLE_HYDRATION_CONTRACT_MISSING')
    current_wallet=getattr(forward,'wallet',None)
    if current_wallet!=expected_wallet or not isinstance(current_wallet,str) or not ADDR.fullmatch(current_wallet):
        raise TargetHold('TARGET_SAVED_WALLET_SIGNER_MISMATCH')
    return old, forward, q25, base_prepare


'''
    hydration = hydration[:a] + hydration[b:]
    hydration = hydration.replace('def exact_native_refresh(', bootstrap + 'def exact_native_refresh(', 1)
    hydration = replace_one(hydration, 'build_state=None):', 'build_state=None, expected_wallet=None):', 'signature')
    hydration = replace_one(hydration, '    candidate=manifest(row,meta)\n',
                            '    candidate=manifest(row,meta)\n'
                            '    if not isinstance(expected_wallet,str) or not ADDR.fullmatch(expected_wallet):\n'
                            "        raise TargetHold('TARGET_EXPECTED_WALLET_REQUIRED')\n"
                            '    old,forward,q25,base_prepare=ensure_exact_builder(provider,candidate,expected_wallet)\n', 'exact_init')
    hydration = replace_one(hydration, '    wallet=getattr(forward,\'wallet\',None)\n',
                            '    wallet=getattr(forward,\'wallet\',None)\n'
                            "    if wallet!=expected_wallet: raise TargetHold('TARGET_SAVED_WALLET_SIGNER_MISMATCH')\n",
                            'post_wallet')
    engine = original[FILES[1]]
    engine = replace_one(engine, "mod('oracle_504_targeted_native_hydration')",
                         "mod('oracle_505_targeted_native_hydration')", 'engine_import')
    engine = replace_one(engine, 'warm_result = exact_hydration.exact_native_refresh(provider,row)',
                         'warm_result = exact_hydration.exact_native_refresh(provider,row,expected_wallet=wallet)', 'engine_call')
    engine = replace_one(engine, "assert 'exact_hydration.exact_native_refresh(provider,row)' in active",
                         "assert 'exact_hydration.exact_native_refresh(provider,row,expected_wallet=wallet)' in active",
                         'engine_fixture')
    engine = replace_one(engine, "'oracle_504_native_engine.json'", "'oracle_505_native_engine.json'", 'engine_report')
    engine = replace_one(engine, "'oracle_504_transient_inbox.json'", "'oracle_505_transient_inbox.json'", 'engine_inbox')
    engine = engine.replace('ORACLE504_EXACT_NATIVE_TARGETED_EXECUTOR', 'ORACLE505_EXACT_NATIVE_TARGETED_EXECUTOR')
    launcher = original[FILES[2]]
    if 'oracle_504_execution_engine' not in launcher:
        raise RuntimeError('HOLD_504_LAUNCHER_ENGINE_NOT_FOUND')
    launcher = launcher.replace('oracle_504_execution_engine', 'oracle_505_execution_engine')
    launcher = replace_one(launcher, "'oracle_504_atomic_sim_machine.json'",
                           "'oracle_505_atomic_sim_machine.json'", 'launcher_report')
    launcher = launcher.replace('ORACLE504', 'ORACLE505')
    if 'broadcast' not in launcher or 'signed_sim' not in launcher:
        raise RuntimeError('HOLD_504_LAUNCHER_GATES_MISSING')
    result = {
        P / 'oracle_505_targeted_native_hydration.py': hydration,
        P / 'oracle_505_execution_engine.py': engine,
        P / 'oracle_505_atomic_sim_machine.py': launcher,
    }
    for path, body in result.items():
        ast.parse(body, filename=str(path))
    assert 'with isolated_target_state(candidate):\n                warm()' in hydration
    assert 'raise Hold(\'TARGET_WARMED_WAIT_NEW_EVENT\')' in engine
    assert 'with native_capacity_scope():provider.prewarm()' not in engine
    assert "'SCANNER_EXACT_TRIPLE_ON_DEMAND_ONLY'" in engine
    assert 'TARGET_SAVED_WALLET_SIGNER_MISMATCH' in hydration
    assert 'broadcast' in engine
    return result


def main():
    files = make()  # Nothing written until every source passes every check.
    P.mkdir(parents=True, exist_ok=True)
    staged = []
    try:
        for dest, body in files.items():
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             suffix='.tmp', prefix='oracle505_',
                                             dir=P, delete=False) as f:
                f.write(body)
                staged.append((Path(f.name), dest))
        for stage, dest in staged:
            os.replace(stage, dest)
    finally:
        for stage, _ in staged:
            stage.unlink(missing_ok=True)
    print('[PASS] ORACLE-505 executor-only full modules installed:', len(files))
    print('[PRESERVE] ORACLE-500 scanner, ORACLE-344 bus, ORACLE-504 sources, Credential Manager')
    print('[GUARD] exact one-pair scoped bootstrap; fresh re-nomination; saved public wallet match')
    print('[MODE] offline install, no signing, no broadcast, no RPC')


if __name__ == '__main__':
    main()
