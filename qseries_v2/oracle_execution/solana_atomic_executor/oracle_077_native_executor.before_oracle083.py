"""ORACLE-077 canonical executor: one scanner, both venue directions.
Uses official-SDK-derived instructions from existing q87; v0 ALT compiler from 074.
No signing or broadcast. No private-key access.
"""

def guard(core):
    if not getattr(core.rpc, '_oracle077_guard', False):
        previous = core.rpc

        def guarded(method, params):
            name = str(method).lower()
            if name.startswith(('send', 'requestairdrop')):
                raise RuntimeError('ORACLE077_BROADCAST_FORBIDDEN')
            return previous(method, params)

        guarded._oracle077_guard = True
        core.rpc = guarded

    def forbidden(*args, **kwargs):
        raise RuntimeError('ORACLE077_SIGNING_OR_BROADCAST_FORBIDDEN')

    core.send = forbidden
    core.signed_tx = forbidden


def compile_native(user, route, core, q87, root, extra_alt=None):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_051_original_scanner_alt_and_size_gate as v51)
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle_074_native_v0_compiler import compile_existing_alt

    guard(core)
    print('[ORACLE051_NATIVE] [ORACLE077_COMPILER_CALLED]', flush=True)

    result = compile_existing_alt(
        user, route, core, q87, root, extra_alt, v51=v51
    )
    # ORACLE080_V1_SIZE_FALLBACK
    if (not result.get('ok') and any(
            'ATOMIC_TX_TOO_LARGE:' in str(a.get('detail', ''))
            for a in (result.get('attempts') or []))):
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_080_v1_atomic_fallback as v80
        result = v80.compile_v1(user, route, core, q87, v51)

    if not isinstance(result, dict):
        raise RuntimeError('ORACLE077_COMPILER_BAD_RESULT')

    print(
        '[ORACLE051_NATIVE] [ORACLE077_NATIVE_RESULT] '
        'ok=%s reason=%s attempts=%d' % (
            bool(result.get('ok')),
            result.get('reason'),
            len(result.get('attempts') or [])
        ),
        flush=True
    )

    if not result.get('ok'):
        for item in (result.get('attempts') or [])[:6]:
            fields = (
                'candidate', 'alt_count', 'alt_check',
                'error', 'detail', 'bytes'
            )
            print(
                '[ORACLE051_NATIVE] [ORACLE077_COMPILE_ATTEMPT]',
                {k: item[k] for k in fields if k in item},
                flush=True
            )

    if result.get('ok'):
        assert len(bytes(result.get('raw') or b'')) <= (4096 if result.get('version') == 1 else 1232)
        assert result.get('start_lamports', 0) >= 10_000_000

    return result


def simulate_native(compiled, user):
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle_076_canonical_money_path import unsigned_atomic_balance_sim

    guard(core)
    result = unsigned_atomic_balance_sim(compiled, user, core)

    if not isinstance(result, dict):
        return {
            'err': 'ORACLE077_SIM_RESULT_INVALID',
            'units': 0,
            'logs': []
        }

    check = result.get('profit_check') or {}

    print(
        '[ORACLE051_SIM] [ORACLE077_SIMULATION] '
        'err=%s units=%s estimate=%s realized=FALSE' % (
            type(result.get('err')).__name__
            if result.get('err') is not None else 'None',
            result.get('units'),
            check.get('estimated_net_lamports')
        ),
        flush=True
    )

    return result
