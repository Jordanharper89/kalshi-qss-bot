from qseries_v2.oracle_adapters.independent.oad_262_solana_live_token_discovery import discover_live_solana_tokens
from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

def discover_distinct_viable_tokens(required=5,timeout_seconds=20.0):
    d=discover_live_solana_tokens(timeout_seconds)
    raw=tuple(d.payload.get("tokens") or ())
    viable=[]
    rejected=[]

    for x in raw:
        token=str(x.get("token_address") or "")
        if not token or token in viable:
            continue

        try:
            e=expand_live_solana_token_pools(
                token_address=token,
                timeout_seconds=timeout_seconds
            )
            if not tuple(e.payload.get("pools") or ()):
                raise RuntimeError("NO_LIVE_POOLS")
        except Exception as z:
            rejected.append((token,type(z).__name__,str(z)))
            continue

        viable.append(token)

        if len(viable)>=required:
            break

    return tuple(viable),tuple(rejected),len(raw)

def acquire_cohort(root=None,episodes=5,cycles=15):
    tokens,rejected,discovered=discover_distinct_viable_tokens(episodes)

    if len(tokens)<episodes:
        raise AssertionError(
            f"insufficient distinct viable tokens: "
            f"viable={len(tokens)} required={episodes} "
            f"discovered={discovered}"
        )

    out=[]

    for j,token in enumerate(tokens,1):
        print(
            f"[SSI-011C-ACQUIRE] episode={j}/{episodes} "
            f"token={token}"
        )

        last=None

        for n in range(1,cycles+1):
            last=run_solana_continuous_cycle(
                root=root,
                cycle=n,
                token_address=token
            )

        hist=tuple(
            read_pinned_pool_history(
                token,
                root=root,
                limit=4096
            )
        )

        if len(hist)<13:
            raise AssertionError(
                f"temporal depth insufficient "
                f"token={token} rows={len(hist)}"
            )

        d={
            "episode":j,
            "token":token,
            "history_records":len(hist),
            "successful_cycles":cycles,
            "temporal_state":"TEMPORAL_5_15_30_60_READY",
            "ready_windows":(5,15,30,60),
            "execution_authority":False,
        }

        print("[SSI-011-EPISODE]",d)
        out.append(d)

    r={
        "episodes":tuple(out),
        "unique_tokens":tokens,
        "independent_tokens":len(tokens),
        "discovered":discovered,
        "rejected":rejected,
        "read_only":True,
        "execution_authority":False,
    }

    print("[SSI-011C]",r)
    return r
