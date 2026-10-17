from __future__ import annotations
"""ORACLE-504: scanner-specified exact native PumpSwap / Meteora warm.

This is executor-local. No scanner process, subscriber, SQLite writer,
key storage, or transaction broadcast is changed. Never trade the initiating
candidate after a warm; await the next fresh canonical event.
"""
import contextlib
import re
from pathlib import Path

ADDR=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

class TargetHold(RuntimeError):
    pass

def classified(phase, exc):
    s=str(exc).lower()
    if any(x in s for x in ('429','rate limit','too many requests','throttl')):
        return TargetHold('TARGET_RPC_429_'+phase)
    return TargetHold('TARGET_'+phase+'_'+type(exc).__name__.upper())

def manifest(row, meta):
    """Only exact scanner source identity is admissible; reject altered pool."""
    if not isinstance(row,dict) or not isinstance(meta,dict):
        raise TargetHold('TARGET_BAD_MANIFEST')
    token,pump,dlmm=(row.get('token'),row.get('pump_pool'),row.get('meteora_pool'))
    if not all(isinstance(v,str) and ADDR.fullmatch(v) for v in (token,pump,dlmm)):
        raise TargetHold('TARGET_BAD_SOURCE_ADDRESS')
    if str(meta.get('address'))!=dlmm:
        raise TargetHold('TARGET_DLMM_POOL_DIFFERS_FROM_SCANNER')
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    if {str(meta.get('token_x')),str(meta.get('token_y'))}!={token,core.WSOL}:
        raise TargetHold('TARGET_DLMM_MINT_PAIR_INVALID')
    for field in ('decimals_x','decimals_y'):
        try:
            n=int(meta[field])
            if n<0 or n>18:raise ValueError()
        except (KeyError,TypeError,ValueError):
            raise TargetHold('TARGET_DLMM_DECIMALS_INVALID') from None
    return {'token':token,'pump_pool':pump,'meteora_pool':dlmm,
            'meteora_meta':dict(meta),'source':'SCANNER_EXACT_NOMINATION'}

@contextlib.contextmanager
def isolated_target_state(candidate):
    """Limit a private executor hydration only; restore all original hooks."""
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as runtime
    old_universe=engine.candidate_universe
    old_cpmm=runtime.rc.discover
    try:
        # The original single-pair native builders consume the SAME object used
        # by the scanner's PairState, but no longer choose different markets.
        engine.candidate_universe=lambda _root:[candidate]
        runtime.rc.discover=lambda _root:[]
        yield
    finally:
        engine.candidate_universe=old_universe
        runtime.rc.discover=old_cpmm

def ensure_exact_builder(provider, candidate, expected_wallet):
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


def exact_native_refresh(provider, row, *, resolve_meta=None, build_state=None, expected_wallet=None):
    """Warm exact scanner triple and native instructions for provider's wallet.

    No mutation of scanner disk / process. Fails closed. Does NOT return a
    reusable old quote: engine must HOLD and wait for a NEW source event.
    """
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    token=row.get('token','')
    if not isinstance(token,str) or not ADDR.fullmatch(token):
        raise TargetHold('TARGET_BAD_TOKEN')
    try:
        meta=resolve_meta(token) if resolve_meta is not None else core.discover_dlmm(token)
    except Exception as exc:
        raise classified('METADATA',exc) from None
    candidate=manifest(row,meta)
    if not isinstance(expected_wallet,str) or not ADDR.fullmatch(expected_wallet):
        raise TargetHold('TARGET_EXPECTED_WALLET_REQUIRED')
    old,forward,q25,base_prepare=ensure_exact_builder(provider,candidate,expected_wallet)
    try:
        # Use scanner's *original* PairState hydrator with just one allowed pair.
        # The cached prepare entry point may have been rebound to an old epoch;
        # _ORIG_PREPARE ensures real fresh account reads, not cached old state.
        with isolated_target_state(candidate):
            state=(build_state or base_prepare)(Path.cwd())
    except Exception as exc:
        raise classified('STATE',exc) from None
    pairs=list(state.get('pairs') or []) if isinstance(state,dict) else []
    if len(pairs)!=1:
        raise TargetHold('TARGET_NOT_EXACTLY_ONE_PAIR')
    pair=pairs[0]
    if (str(getattr(pair,'token',None)),str(getattr(pair,'pump_pool',None)),
        str(getattr(pair,'meteora_pool',None)))!=(candidate['token'],candidate['pump_pool'],candidate['meteora_pool']):
        raise TargetHold('TARGET_HYDRATED_TRIPLE_MISMATCH')
    wallet=getattr(forward,'wallet',None)
    if wallet!=expected_wallet: raise TargetHold('TARGET_SAVED_WALLET_SIGNER_MISMATCH')
    if not isinstance(wallet,str) or not ADDR.fullmatch(wallet):
        raise TargetHold('TARGET_PROVIDER_WALLET_INVALID')
    try:
        q25.bind_cached_state(state)
    except Exception as exc:
        raise classified('BIND',exc) from None
    try:
        warmed=old.install_proven_hot_math(state)
    except Exception as exc:
        raise classified('HOT_MATH',exc) from None
    try:
        old.prebuild_templates(state,wallet)
    except Exception as exc:
        raise classified('PUMP_NATIVE',exc) from None
    try:
        old.prebuild_meteora_templates(state,wallet,warmed)
    except Exception as exc:
        raise classified('DLMM_NATIVE',exc) from None
    # Publish native registry only AFTER both native template passes finished.
    forward.state=state
    forward.pairs={candidate['token']:pair}
    forward.indexes={candidate['token']:0}
    forward.programs={str(x['token']):str(x['program']) for x in warmed}
    provider.last_replenish=__import__('time').monotonic()
    provider.refresh_attempts=getattr(provider,'refresh_attempts',0)+1
    return {'token':candidate['token'],'pump_pool':candidate['pump_pool'],
            'meteora_pool':candidate['meteora_pool'],'warm_complete':True,
            'reuse_triggering_nomination':False,'broadcast':False}

def tests():
    """Pure deterministic source contract, zero RPC and no private keys."""
    import ast, inspect
    from pathlib import Path
    s=Path(__file__).read_text(encoding='utf-8')
    ast.parse(s)
    assert 'engine.candidate_universe=old_universe' in s
    assert 'runtime.rc.discover=old_cpmm' in s
    assert 'forward.pairs={candidate' in s
    assert 'send_transaction(' not in s.split('def tests():')[0] and 'sendTransaction(' not in s.split('def tests():')[0]
    assert not any(z in s.split('def tests():')[0] for z in ('private_key=', 'QSB_SOLANA_PRIVATE_KEY'))
    # No calls to the actual RPC or native SDK in this self-test.
    assert classified('METADATA',RuntimeError('rate limit: 429')).args[0]=='TARGET_RPC_429_METADATA'
    assert classified('DLMM_NATIVE',ValueError('wrong')).args[0]=='TARGET_DLMM_NATIVE_VALUEERROR'
    print('[PASS] ORACLE504 exact-pair manifest, bounded native source and no broadcast')

if __name__=='__main__':tests()
