from __future__ import annotations

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint2_forward_atomic_sim as cp


def _reverse_opportunity(snap):
    rows = list(
        r.q18.exact_snapshot_opportunities(
            snap,
            0.001,
        )
    )

    for row in rows:
        if row.get("direction") == "METEORA_TO_PUMP":
            return row

    raise RuntimeError("NO_METEORA_TO_PUMP_OPPORTUNITY")



def _build_meteora_reverse_ix_hot(
    token,
    input_amount,
    quote_result,
):
    import base64
    import struct

    template = r.METEORA_TEMPLATES.get(str(token))

    if template is None:
        raise RuntimeError(
            "METEORA_TEMPLATE_MISSING:" + str(token)
        )

    forward_swap = bool(template["swap_for_y"])
    reverse_swap = not forward_swap
    quote_swap = bool(quote_result.get("swap_for_y"))

    if quote_swap != reverse_swap:
        raise RuntimeError(
            "REVERSE_DLMM_QUOTE_DIRECTION_MISMATCH"
        )

    accounts = list(template["fixed_accounts"])

    if len(accounts) < 6:
        raise RuntimeError("METEORA_TEMPLATE_ACCOUNTS_SHORT")

    # Warm template is token -> WSOL.
    # Reverse economic direction is WSOL -> token.
    accounts[4], accounts[5] = accounts[5], accounts[4]

    arrays = list(template["arrays"])
    crossed = max(
        1,
        int(quote_result.get("bins_crossed") or 1),
    )

    n = min(
        len(arrays),
        max(1, (crossed + 69) // 70),
    )

    chosen = (
        arrays[:n]
        if reverse_swap
        else list(reversed(arrays))[:n]
    )

    accounts.extend(
        (address, False, True)
        for _, address in chosen
    )

    min_out = (
        int(quote_result["raw_out"])
        * (10000 - r.q87.las.q59.SLIPPAGE_BPS)
        // 10000
    )

    data = (
        bytes([248,198,158,145,225,117,135,200])
        + struct.pack(
            "<QQ",
            int(input_amount),
            int(min_out),
        )
    )

    return {
        "programId": r.q87.c.DLMM,
        "accounts": [
            {
                "pubkey": pubkey,
                "isSigner": signer,
                "isWritable": writable,
            }
            for pubkey, signer, writable in accounts
        ],
        "data": base64.b64encode(data).decode(),
    }

def _reverse_route(user, snap, reverse):
    token = str(reverse["token"])
    start = int(reverse["start"])
    token_in = int(
        reverse.get("net_token")
        or reverse.get("gross_token")
        or 0
    )

    if token_in <= 0:
        raise RuntimeError("REVERSE_TOKEN_INPUT_ZERO")

    meteora_ix = _build_meteora_reverse_ix_hot(
        token,
        start,
        dict(reverse["mq"]),
    )

    pump64, expected_quote = r.q87.c.pump_sell_tx(
        user,
        token,
        token_in,
    )

    pump_ixs, base_alts = r.q87.c.resolve_pump_instructions(
        pump64
    )

    pump_positions = [
        i
        for i, ix in enumerate(pump_ixs)
        if ix.get("programId") == r.q87.c.PUMP
    ]

    if len(pump_positions) != 1:
        raise RuntimeError(
            "REVERSE_PUMP_PROGRAM_IX_COUNT:%d"
            % len(pump_positions)
        )

    pi = pump_positions[0]
    pump_ix = pump_ixs[pi]

    if not any(
        a.get("pubkey") == snap["pump_pool"]
        for a in (pump_ix.get("accounts") or [])
    ):
        raise RuntimeError("REVERSE_PUMP_POOL_ACCOUNT_DRIFT")

    pre = list(pump_ixs[:pi])
    post = list(pump_ixs[pi + 1:])

    # Pump helper/setup instructions remain first so ATAs/WSOL
    # prerequisites exist. Economic order is then:
    # Meteora WSOL->token, Pump token->WSOL.
    full = pre + [meteora_ix, pump_ix] + post

    return {
        "token": token,
        "direction": "METEORA_TO_PUMP",
        "start_lamports": start,
        "pre_sim_net_lamports": int(reverse["local_net"]),
        "pre_sim_bps": float(reverse["local_bps"]),
        "meteora_token_out_raw": token_in,
        "pump_expected_quote_raw": int(expected_quote),
        "pump_ixs": pump_ixs,
        "pump_index": pi + 1,
        "pump_ix": pump_ix,
        "meteora_ix": meteora_ix,
        "base_alts": list(base_alts),
        "original_candidates": [
            ("FULL_REVERSE", full),
        ],
    }


def compile_reverse(user, snap):
    reverse = _reverse_opportunity(snap)

    print(
        "[CHECKPOINT3_REVERSE_ROUTE] "
        "token=%s bps=%+.2f net=%+d token_in=%d"
        % (
            str(reverse["token"])[:10],
            float(reverse["local_bps"]),
            int(reverse["local_net"]),
            int(
                reverse.get("net_token")
                or reverse.get("gross_token")
                or 0
            ),
        ),
        flush=True,
    )

    route = _reverse_route(
        user,
        snap,
        reverse,
    )

    result = r.compile_current(
        user,
        route,
    )

    if not result.get("ok"):
        print(
            "[CHECKPOINT3_REVERSE_COMPILE_FAIL] %s"
            % result,
            flush=True,
        )
        return result

    size = int(result.get("bytes") or 0)

    print(
        "[CHECKPOINT3_REVERSE_COMPILE_PASS] "
        "candidate=%s bytes=%d max=1232"
        % (
            result.get("candidate"),
            size,
        ),
        flush=True,
    )

    if size > 1232:
        raise RuntimeError(
            "REVERSE_COMPILED_TOO_LARGE:%d"
            % size
        )

    print(
        "[CHECKPOINT3_REVERSE_ATOMIC_ORDER] "
        "METEORA_TO_PUMP=True",
        flush=True,
    )
    print(
        "[SIMULATION] skipped_balance_independent_compile_only",
        flush=True,
    )
    print("[BROADCAST] disabled", flush=True)

    return {
        "ok": True,
        "direction": "METEORA_TO_PUMP",
        "bytes": size,
        "candidate": result.get("candidate"),
        "simulation": False,
        "broadcast": False,
    }



class _Checkpoint3Complete(Exception):
    pass



class _Checkpoint3Complete(Exception):
    pass


def main():
    captured={}
    original=r._execute_route_once

    def checkpoint3_intercept(user,snap,_forward):
        captured["result"]=compile_reverse(user,snap)
        raise _Checkpoint3Complete()

    r._execute_route_once=checkpoint3_intercept

    try:
        try:
            cp.main()
        except _Checkpoint3Complete:
            pass
    finally:
        r._execute_route_once=original

    result=captured.get("result")

    if not isinstance(result,dict):
        raise RuntimeError(
            "CHECKPOINT3_REVERSE_ROUTE_NOT_MATERIALIZED"
        )

    if not result.get("ok"):
        print(
            "[CHECKPOINT3_REVERSE_FINAL] status=FAIL",
            flush=True,
        )
        return 1

    print(
        "[CHECKPOINT3_REVERSE_FINAL] "
        "status=PASS bytes=%d"
        %int(result.get("bytes") or 0),
        flush=True,
    )
    print(
        "[CHECKPOINT3_HARNESS] "
        "checkpoint2_bootstrap_only=True "
        "simulation_fallthrough=False",
        flush=True,
    )
    print("[BROADCAST] disabled",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
