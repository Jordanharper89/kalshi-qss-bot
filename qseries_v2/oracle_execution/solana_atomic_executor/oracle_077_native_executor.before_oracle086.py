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


# ORACLE083_EXACT_SIMULATION_FAILURE_TRACE
_oracle083_original_simulate = simulate_native

def simulate_native(compiled, user):
    import json
    import re
    from pathlib import Path

    result = _oracle083_original_simulate(compiled, user)
    if not isinstance(result, dict):
        return result

    err = result.get("err")
    if err is None:
        print("[ORACLE083_SIM] SUCCESS", flush=True)
        return result

    def safe(value):
        if isinstance(value, dict):
            return {str(k): safe(v) for k, v in value.items()
                    if str(k).lower() not in (
                        "raw", "transaction", "signature", "secret",
                        "private_key", "rpc_url", "api_key")}
        if isinstance(value, (list, tuple)):
            return [safe(v) for v in value[:20]]
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        text = str(value)
        text = re.sub(r"https?://\\S+", "[URL_REDACTED]", text)
        text = re.sub(r"(?i)api.key[=:][^\\s&]+", "api_key=[REDACTED]", text)
        return text[:350]

    logs = result.get("logs") or []
    selected = []
    for line in logs:
        text = str(line)
        if any(word in text.lower() for word in (
                "invoke", "failed", "error", "consumed",
                "instruction:", "program log:", "success")):
            selected.append(safe(text))

    index = None
    if isinstance(err, dict):
        instruction = err.get("InstructionError")
        if isinstance(instruction, (list, tuple)) and instruction:
            index = instruction[0]

    payload = {
        "status": "UNSIGNED_SIMULATION_REJECTED",
        "instruction_index": index,
        "error": safe(err),
        "units": safe(result.get("units")),
        "log_count": len(logs),
        "program_trace": selected[-60:],
        "execution_authority": False,
        "broadcast": False,
        "realized_profit": False,
    }
    path = Path("runtime_state/oracle/oracle_live_execution/oracle_083_sim_failure.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print("[ORACLE083_FAILURE]", json.dumps(payload, sort_keys=True), flush=True)
    print("[ORACLE083_REPORT]", path, flush=True)
    return result
